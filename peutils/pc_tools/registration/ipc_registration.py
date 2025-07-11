import json
import open3d as o3d
import numpy as np
import os


def load_point_cloud(filepath):
    """
    加载PCD点云文件。
    """
    try:
        pcd = o3d.io.read_point_cloud(filepath)
        if not pcd.has_points():
            print(f"警告: 文件 {filepath} 加载的点云为空。")
            return None
        return pcd
    except Exception as e:
        print(f"错误: 加载 {filepath} 失败: {e}")
        return None


def preprocess_point_cloud(pcd, voxel_size, nb_neighbors, std_ratio, frame_id="N/A"):
    """
    对点云进行预处理：下采样、离群点去除和计算法线。
    包含详细的调试信息和空点云检查。
    """
    original_point_count = len(pcd.points)
    print(f"DEBUG (帧 {frame_id}): 原始点云数量: {original_point_count}")
    # 移除 NaN/Inf 点 ---
    points_np = np.asarray(pcd.points)
    valid_mask = ~np.any(np.isnan(points_np), axis=1) & ~np.any(
        np.isinf(points_np), axis=1
    )

    # 如果存在无效点
    if not np.all(valid_mask):
        invalid_count = np.sum(~valid_mask)
        print(f"警告 (帧 {frame_id}): 发现并移除了 {invalid_count} 个包含 NaN/Inf 的点。")
        pcd.points = o3d.utility.Vector3dVector(points_np[valid_mask])
        if not pcd.has_points():
            print(f"错误 (帧 {frame_id}): 移除 NaN/Inf 后点云为空。")
            return None

    # 1. 体素下采样
    pcd_down = pcd.voxel_down_sample(voxel_size=voxel_size)
    downsampled_point_count = len(pcd_down.points)
    print(
        f"DEBUG (帧 {frame_id}): 体素下采样后 (voxel_size={voxel_size}): {downsampled_point_count} 个点"
    )

    if downsampled_point_count == 0:
        print(f"错误 (帧 {frame_id}): **体素下采样后点云为空。请增大原始点云密度或减小 VOXEL_SIZE。**")
        return None

    # 2. 统计学离群点移除
    # 确保 nb_neighbors 不大于当前点云的数量，否则会报错或行为异常
    actual_nb_neighbors = min(
        nb_neighbors, downsampled_point_count - 1 if downsampled_point_count > 0 else 0
    )
    if actual_nb_neighbors <= 0:
        print(f"警告 (帧 {frame_id}): 无法进行离群点移除，点云数量太少 ({downsampled_point_count} 点)。")
        pcd_processed = pcd_down  # 跳过离群点移除
    else:
        pcd_processed, ind = pcd_down.remove_statistical_outlier(
            nb_neighbors=actual_nb_neighbors, std_ratio=std_ratio
        )

    outlier_removed_point_count = len(pcd_processed.points)
    print(
        f"DEBUG (帧 {frame_id}): 统计学离群点移除后 (nb_neighbors={actual_nb_neighbors}, std_ratio={std_ratio}): {outlier_removed_point_count} 个点"
    )

    if outlier_removed_point_count == 0:
        print(f"错误 (帧 {frame_id}): **离群点移除后点云为空。请减小 NB_NEIGHBORS 或增大 STD_RATIO。**")
        return None

    # 3. 估算法线
    # 估算法线的 radius 通常设置为 voxel_size 的 2-5 倍，max_nn 确保能找到足够的邻居
    search_param = o3d.geometry.KDTreeSearchParamHybrid(
        radius=voxel_size * 3.0, max_nn=30
    )
    pcd_processed.estimate_normals(search_param=search_param)

    if not pcd_processed.has_normals():
        print(f"错误 (帧 {frame_id}): **未能成功估算法线。请检查点云密度或调整法线估计参数 (radius/max_nn)。**")
        # 即使法线估计失败，ICP也可以用PointToPoint方法来计算，但是目前使用的是PointToPlane方法，依赖法线，所以强制返回None
        return None

    # 4. 统一法线方向 (可选，但推荐对于 PointToPlane ICP)
    # 对于LiDAR数据，通常法线指向传感器方向。假设LiDAR在车辆顶部，大致向上
    # 这里我们只确保它们方向一致，例如指向同一个半球
    pcd_processed.orient_normals_consistent_tangent_plane(k=20)  # k是邻居数量

    return pcd_processed


def pairwise_registration(
    source, target, max_correspondence_distance, initial_transform=np.identity(4)
):
    """
    使用ICP算法计算两个点云之间的配准。
    source: 源点云 (moving point cloud)
    target: 目标点云 (fixed point cloud)
    max_correspondence_distance: 对应点对的最大距离
    initial_transform: 初始变换矩阵（对ICP非常重要）
    """
    # 使用 PointToPlane 估计方法，因为它通常比 PointToPoint 更稳定和准确
    # 要求 source 和 target 都必须有法线
    estimation_method = (
        o3d.pipelines.registration.TransformationEstimationPointToPlane()
    )

    # ICP 迭代参数
    # max_iteration: 最大迭代次数，适当增加，但过高可能陷入局部最优或耗时
    # relative_fitness / relative_rmse: 收敛阈值，当 fitness 或 RMSE 变化小于此值时停止
    criteria = o3d.pipelines.registration.ICPConvergenceCriteria(
        max_iteration=300,  # 适当迭代次数
        relative_fitness=1e-6,  # 匹配点的比例变化，更小的值表示更严格的收敛
        relative_rmse=1e-6,  # 均方根误差变化，更小的值表示更严格的收敛
    )

    reg_result = o3d.pipelines.registration.registration_icp(
        source,
        target,
        max_correspondence_distance,
        initial_transform,
        estimation_method,
        criteria,
    )
    return reg_result.transformation, reg_result.fitness, reg_result.inlier_rmse


def main(
    pcd_files,
    voxel_size=0.5,
    max_corr_dist_factor=1.5,
    outlier_nb_neighbors=20,
    outlier_std_ratio=2.0,
    fitness_threshold=0.3,
    retry_max_correspondence_distance_factor=1.5,
    retry_fitness_threshold_factor=0.8,
):
    if not pcd_files:
        print("错误: 未找到任何PCD文件。请检查文件夹路径和文件类型。")
        return []

    print(f"找到 {len(pcd_files)} 个PCD文件。")

    global_poses = []
    # 初始化第一帧的全局位姿为单位矩阵
    current_global_transform = np.identity(4)
    global_poses.append(current_global_transform)

    # 计算ICP的最大对应距离：通常是体素大小的几倍
    max_correspondence_distance = voxel_size * max_corr_dist_factor
    print(f"ICP最大对应距离设置为: {max_correspondence_distance:.3f} 米")

    # 1. 加载并预处理第一帧
    print(f"\n--- 处理第 0 帧: {os.path.basename(pcd_files[0])} ---")
    prev_pcd = load_point_cloud(pcd_files[0])
    if prev_pcd is None:
        return []

    prev_pcd_processed = preprocess_point_cloud(
        prev_pcd, voxel_size, outlier_nb_neighbors, outlier_std_ratio, frame_id="0"
    )
    if prev_pcd_processed is None:
        print("错误: 第一帧预处理失败，无法继续。")
        return []

    # 用于下一帧 ICP 的初始变换预测（运动模型）
    # 假设匀速运动，用上次计算的帧间相对变换作为下次的初始猜测
    estimated_relative_transform_curr_to_prev = np.identity(4)

    # 2. 迭代处理后续帧
    for i in range(1, len(pcd_files)):
        print(f"\n--- 处理第 {i} 帧: {os.path.basename(pcd_files[i])} ---")
        curr_pcd = load_point_cloud(pcd_files[i])
        if curr_pcd is None:
            # 如果当前帧加载失败，跳过，并尝试使用前一帧的运动模型来估计其位姿
            print(f"警告: 帧 {i} 加载失败，跳过配准，使用前一帧的运动模型估算位姿。")
            current_global_transform = np.dot(
                current_global_transform, estimated_relative_transform_curr_to_prev
            )
            global_poses.append(current_global_transform)
            continue

        curr_pcd_processed = preprocess_point_cloud(
            curr_pcd,
            voxel_size,
            outlier_nb_neighbors,
            outlier_std_ratio,
            frame_id=str(i),
        )
        if curr_pcd_processed is None:
            print(f"警告: 帧 {i} 预处理失败，跳过配准，使用前一帧的运动模型估算位姿。")
            current_global_transform = np.dot(
                current_global_transform, estimated_relative_transform_curr_to_prev
            )
            global_poses.append(current_global_transform)
            continue

        # 模板目标是计算T_curr_to_prev,所以source 是 curr_pcd，target 是 prev_pcd
        # ICP 接受初始猜测参数initial_transform，内容是将source变换到target的初始猜测,可以是单位矩阵，或者更复杂的基于IMU的预测
        # 我们这里使用基于运动模型的初始变换
        # 如果我们假设匀速运动，那么 T_{i-1, i-2} (上一次的相对变换) 应该约等于 T_{i, i-1}
        # 所以初始猜测就是使用上一次计算得出的结果,即estimated_relative_transform_curr_to_prev
        initial_transform_for_pairwise = estimated_relative_transform_curr_to_prev

        # 计算当前帧相对于上一帧的变换 (T_curr_to_prev)
        relative_transform_curr_to_prev, fitness, rmse = pairwise_registration(
            curr_pcd_processed,
            prev_pcd_processed,
            max_correspondence_distance,
            initial_transform=initial_transform_for_pairwise,  # 传入初始变换
        )
        print(f"  ICP 结果: Fitness = {fitness:.4f}, RMSE = {rmse:.4f}")

        if fitness < fitness_threshold:  # ICP 匹配度过低，认为配准失败
            print(
                f"警告: 帧 {i} ICP 配准失败 (Fitness {fitness:.4f} 低于阈值 {fitness_threshold:.4f})。"
            )
            print("尝试使用更宽松的参数重试 ICP。")

            retry_max_correspondence_distance = (
                max_correspondence_distance * retry_max_correspondence_distance_factor
            )  # 尝试使用更大的对应距离重试
            retry_fitness_threshold = (
                fitness_threshold * retry_fitness_threshold_factor
            )  # 尝试降低对匹配度的要求，但不能太低

            # 重新运行 ICP
            (
                retry_transform_curr_to_prev,
                retry_fitness,
                retry_rmse,
            ) = pairwise_registration(
                curr_pcd_processed,
                prev_pcd_processed,
                retry_max_correspondence_distance,
                initial_transform=initial_transform_for_pairwise,
            )

            if retry_fitness >= retry_fitness_threshold:
                print(f"  重试成功！Fitness = {retry_fitness:.4f}, RMSE = {retry_rmse:.4f}")
                transform_curr_to_prev = retry_transform_curr_to_prev
                estimated_relative_transform_curr_to_prev = transform_curr_to_prev
            else:
                print(
                    f"  重试失败 (Fitness {retry_fitness:.4f} 仍低于阈值 {retry_fitness_threshold:.4f})。"
                )
                print("  将沿用前一帧的运动模型估算位姿。这将导致误差累积！")
                transform_curr_to_prev = estimated_relative_transform_curr_to_prev
        else:
            transform_curr_to_prev = relative_transform_curr_to_prev
            # 更新下一帧的初始变换预测
            estimated_relative_transform_curr_to_prev = transform_curr_to_prev

        # 更新全局位姿
        # T_{i,0} = T_{i-1,0} * T_{i,i-1}
        current_global_transform = np.dot(
            current_global_transform, transform_curr_to_prev
        )
        global_poses.append(current_global_transform)

        # 更新上一帧点云为当前帧，为下一次迭代做准备
        prev_pcd_processed = curr_pcd_processed

    return global_poses


def registration(
    pcd_files,
    voxel_size,
    max_corr_dist_factor,
    outlier_nb_neighbors,
    outlier_std_ratio,
    fitness_threshold,
    retry_max_correspondence_distance_factor,
    retry_fitness_threshold_factor,
    output_file,
):
    """
    :param pcds: 点云文件列表
    :param voxel_size: 体素下采样大小。影响点云密度和计算速度。太大易为空。
                       对于LiDAR数据，常见值在0.1米到0.5米之间。
    :param max_corr_dist_factor: ICP对应点对的最大距离 = VOXEL_SIZE * FACTOR。
                                 决定了匹配点的搜索范围。太小找不到匹配，太大找到错误匹配。
                                 通常设置为 VOXEL_SIZE 的 1.5 到 3 倍
    :param outlier_nb_neighbors: 统计离群点时考虑的邻居数量。太小可能不过滤噪声，太大可能移除合法稀疏点。
    :param outlier_std_ratio: 标准差倍数。数值越大，过滤器越宽松,保留更多点,越小，过滤器越严,移除更多点
    :param fitness_threshold: ICP 结果的最低匹配度阈值。
                              如果匹配度低于此值，认为当前帧配准失败
                              范围通常在0.3-0.5 之间
    :param retry_max_correspondence_distance_factor: 第一次计算失败后，重试时ICP最大对应距离的调整因子
    :param retry_fitness_threshold_factor: 第一次计算失败后，重试时ICP结果的最低匹配度阈值的调整因子
    :param output_file: 输出的pose文件
    :return:
    """
    print("\n--- 开始进行点云配准 ---")
    print(
        f"预处理参数: VOXEL_SIZE={voxel_size}, NB_NEIGHBORS={outlier_nb_neighbors}, STD_RATIO={outlier_std_ratio}"
    )
    print(
        f"ICP参数: MAX_CORR_DISTANCE_FACTOR={max_corr_dist_factor}, FITNESS_THRESHOLD={fitness_threshold}"
    )
    print(
        f"ICP重试参数: RETRY_MAX_CORRESPONDENCE_DISTANCE_FACTOR={retry_max_correspondence_distance_factor}, RETRY_FITNESS_THRESHOLD_FACTOR={retry_fitness_threshold_factor}"
    )

    poses = main(
        pcd_files,
        voxel_size=voxel_size,
        max_corr_dist_factor=max_corr_dist_factor,
        outlier_nb_neighbors=outlier_nb_neighbors,
        outlier_std_ratio=outlier_std_ratio,
        fitness_threshold=fitness_threshold,
        retry_max_correspondence_distance_factor=retry_max_correspondence_distance_factor,
        retry_fitness_threshold_factor=retry_fitness_threshold_factor,
    )

    if not poses:
        print("未能计算出位姿。请检查输入和参数。")
        return
    else:
        print("位姿计算成功")

    with open(output_file, "w") as f:
        json.dump([p.tolist() for p in poses], f, ensure_ascii=False, indent=4)


# ----------------------------------------------------------------------------------------------------------------------

# pcd_folder = "/Users/rxu/Documents/Qinghua/LaneTest/pcd"
# pcd_files = sorted(
#     [os.path.join(pcd_folder, f) for f in os.listdir(pcd_folder) if f.endswith(".pcd")]
# )
# voxel_size = 0.1
# outlier_nb_neighbors = 20
# outlier_std_ratio = 2.0
# max_corr_dist_factor = 0.3
# fitness_threshold = 0.3
# retry_max_correspondence_distance_factor = 1.5
# retry_fitness_threshold_factor = 0.8
# output_file = "pose.json"
#
# registration(
#     pcd_files=pcd_files,
#     voxel_size=voxel_size,
#     max_corr_dist_factor=max_corr_dist_factor,
#     outlier_nb_neighbors=outlier_nb_neighbors,
#     outlier_std_ratio=outlier_std_ratio,
#     fitness_threshold=fitness_threshold,
#     retry_max_correspondence_distance_factor=retry_max_correspondence_distance_factor,
#     retry_fitness_threshold_factor=retry_fitness_threshold_factor,
#     output_file=output_file,
# )

# ----------------------------------------------------------------------------------------------------------------------
