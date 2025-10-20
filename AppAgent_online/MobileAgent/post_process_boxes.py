import copy
import math
import re

def filter_blocks(coordinates, texts=None, image_width=1080, image_height=2220, iou_threshold=0.5,
                       area_threshold=(0.00025, 1), aspect_threshold=(0.0025, 1)):
    filtered_coordinates = copy.deepcopy(coordinates)
    filtered_texts = copy.deepcopy(texts)
    index_to_remove = set()

    # 按size过滤bounding box
    for i, coordinate in enumerate(filtered_coordinates):
        x1, y1, x2, y2 = coordinate
        width = x2 - x1
        height = y2 - y1
        area = width * height
        min_aspect = min(width, height)

        if area < area_threshold[0] * image_width * image_height:
            index_to_remove.add(i)
        elif area > area_threshold[1] * image_width * image_height:
            index_to_remove.add(i)
        elif min_aspect < aspect_threshold[0] * image_height:
            index_to_remove.add(i)
        elif height > aspect_threshold[1] * image_height:
            index_to_remove.add(i)
        elif width > aspect_threshold[1] * image_width:
            index_to_remove.add(i)

    # # 按IoU过滤bounding box
    # for i, coordinate in enumerate(filtered_coordinates):
    #     if i in index_to_remove:
    #         continue
    #     for j, other_coordinate in enumerate(filtered_coordinates):
    #         if j in index_to_remove:
    #             continue
    #         if i == j:
    #             continue
    #         iou, _ = box_iou(coordinate, other_coordinate)
    #         if iou > iou_threshold:
    #             index_to_remove.add(j)

    filtered_coordinates = [coordinate for idx, coordinate in enumerate(filtered_coordinates) if idx not in index_to_remove]
    if filtered_texts is not None:
        filtered_texts = [text for idx, text in enumerate(filtered_texts) if idx not in index_to_remove]
        return filtered_coordinates, filtered_texts
    else:
        return filtered_coordinates


def merge_text_blocks(text_list, coordinates_list):
    merged_text_blocks = []
    merged_coordinates = []

    sorted_indices = sorted(range(len(coordinates_list)),
                            key=lambda k: (coordinates_list[k][1], coordinates_list[k][0]))
    sorted_text_list = [text_list[i] for i in sorted_indices]
    sorted_coordinates_list = [coordinates_list[i] for i in sorted_indices]

    num_blocks = len(sorted_text_list)
    merge = [False] * num_blocks

    for i in range(num_blocks):
        if merge[i]:
            continue

        anchor = i

        group_text = [sorted_text_list[anchor]]
        group_coordinates = [sorted_coordinates_list[anchor]]

        for j in range(i + 1, num_blocks):
            if merge[j]:
                continue

            font_size_anchor = sorted_coordinates_list[anchor][3] - sorted_coordinates_list[anchor][1]
            font_size_j = sorted_coordinates_list[j][3] - sorted_coordinates_list[j][1]
            mean_font_size = (font_size_anchor + font_size_j) / 2
            min_font_size = min(font_size_anchor, font_size_j)

            row_dist_range = [
                0.25 * min_font_size,
                0.5 * min_font_size
            ]
            left_dist_th = 0.25 * min_font_size

            # if abs(sorted_coordinates_list[anchor][0] - sorted_coordinates_list[j][0]) < 10 and \
            #         sorted_coordinates_list[j][1] - sorted_coordinates_list[anchor][3] >= -10 and \
            #         sorted_coordinates_list[j][1] - sorted_coordinates_list[anchor][3] < 30 and \
            #         abs(sorted_coordinates_list[anchor][3] - sorted_coordinates_list[anchor][1] - (
            #                 sorted_coordinates_list[j][3] - sorted_coordinates_list[j][1])) < 10:
            # # if abs(sorted_coordinates_list[anchor][0] - sorted_coordinates_list[j][0]) < left_dist_th and \
            # #         sorted_coordinates_list[j][1] - sorted_coordinates_list[anchor][3] >= -row_dist_range[0] and \
            # #         sorted_coordinates_list[j][1] - sorted_coordinates_list[anchor][3] < row_dist_range[1] and \
            # #         (font_size_anchor / font_size_j < 1.2) and (font_size_j / font_size_anchor > 1.2):
            #     group_text.append(sorted_text_list[j])
            #     group_coordinates.append(sorted_coordinates_list[j])
            #     merge[anchor] = True
            #     anchor = j
            #     merge[anchor] = True

            condition1 = (font_size_anchor / font_size_j < 1.2) and (font_size_j / font_size_anchor < 1.2)
            condition2 = abs(sorted_coordinates_list[anchor][0] - sorted_coordinates_list[j][0]) < left_dist_th
            condition3 = sorted_coordinates_list[j][1] - sorted_coordinates_list[anchor][3] >= -row_dist_range[0]
            condition4 = sorted_coordinates_list[j][1] - sorted_coordinates_list[anchor][3] < row_dist_range[1]

            if condition1 and condition2 and condition3 and condition4:
                group_text.append(sorted_text_list[j])
                group_coordinates.append(sorted_coordinates_list[j])
                merge[anchor] = True
                anchor = j
                merge[anchor] = True

        merged_text = "\n".join(group_text)
        min_x1 = min(group_coordinates, key=lambda x: x[0])[0]
        min_y1 = min(group_coordinates, key=lambda x: x[1])[1]
        max_x2 = max(group_coordinates, key=lambda x: x[2])[2]
        max_y2 = max(group_coordinates, key=lambda x: x[3])[3]

        merged_text_blocks.append(merged_text)
        merged_coordinates.append([min_x1, min_y1, max_x2, max_y2])

    return merged_text_blocks, merged_coordinates


def merge_text_and_icon_blocks(text_coordinates, icon_coordinates):

    # 如果icon和text的bounding box的iou大于0.5，删除text
    text_to_remove = set()
    for i, icon_coordinate in enumerate(icon_coordinates):
        for j, text_coordinate in enumerate(text_coordinates):
            iou, io1, io2 = box_iou(icon_coordinate, text_coordinate)
            if iou > 0.5:
                text_to_remove.add(j)
    text_coordinates = [text_coordinate for idx, text_coordinate in enumerate(text_coordinates) if idx not in text_to_remove]

    return text_coordinates + icon_coordinates


def remove_icon_near_boundary(icon_coordinates, image_width, image_height, th=5):
    icon_to_remove = set()
    for i, icon_coordinate in enumerate(icon_coordinates):
        x1, y1, x2, y2 = icon_coordinate
        if x1 < th or y1 < th or image_width - x2 < th or image_height - y2 < th:
            icon_to_remove.add(i)
    icon_coordinates = [icon_coordinate for idx, icon_coordinate in enumerate(icon_coordinates) if idx not in icon_to_remove]
    return icon_coordinates


def remove_text_in_icon(text_coordinates, icon_coordinates, io_th=0.5, iou_th=0.5):
    # 如果icon在text里的面积大于icon的面积的0.5，删除icon
    icon_to_remove = set()
    for i, icon_coordinate in enumerate(icon_coordinates):
        for j, text_coordinate in enumerate(text_coordinates):
            iou, io1, io2 = box_iou(icon_coordinate, text_coordinate)
            if io1 > io_th and iou < iou_th:
                icon_to_remove.add(i)
    icon_coordinates = [icon_coordinate for idx, icon_coordinate in enumerate(icon_coordinates) if idx not in icon_to_remove]
    return icon_coordinates


def has_consecutive_characters(s):
    # 匹配连续的两个汉字的正则表达式
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]{2}')
    # 匹配连续的两个英文字母的正则表达式
    english_pattern = re.compile(r'[a-zA-Z]{2}')
    # 匹配连续的两个数字的正则表达式
    digit_pattern = re.compile(r'\d{2}')

    # 查找是否有连续的两个汉字
    chinese_match = chinese_pattern.search(s)
    # 查找是否有连续的两个英文字母
    english_match = english_pattern.search(s)
    # 查找是否有连续的两个数字
    digit_match = digit_pattern.search(s)

    # 判断是否有匹配的结果
    return bool(chinese_match) or bool(english_match) or bool(digit_match)


def overlap(box1, box2):
    # 判断两个bounding box是否重叠
    if box1[2] <= box2[0] or box1[0] >= box2[2] or box1[3] <= box2[1] or box1[1] >= box2[3]:
        return False
    return True


def box_iou(box1, box2):
    # 计算两个bounding box的iou
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])

    if area1 == 0 or area2 == 0:
        return 0, 0, 0

    return intersection / (area1 + area2 - intersection), intersection / area1, intersection / area2


def box_distance(box1, box2, overlap_th=0.95, side_center_th=30):
    # # 计算两个bounding box最近处的距离
    # left = box2[0] - box1[2]
    # right = box1[0] - box2[2]
    # top = box2[1] - box1[3]
    # bottom = box1[1] - box2[1]
    #
    # horizontal_dist = max(left, right, 0)
    # vertical_dist = max(top, bottom, 0)

    h_overlap = min(box1[2], box2[2]) - max(box1[0], box2[0])
    v_overlap = min(box1[3], box2[3]) - max(box1[1], box2[1])

    x1 = (box1[0] + box1[2]) / 2
    y1 = (box1[1] + box1[3]) / 2
    x2 = (box2[0] + box2[2]) / 2
    y2 = (box2[1] + box2[3]) / 2

    dist1 = 10000
    dist2 = 10000
    h_or_v = "h"
    if h_overlap > overlap_th * min(box1[2] - box1[0], box2[2] - box2[0]):
        if abs(x1 - x2) < side_center_th:
            dist1 = max(box1[1], box2[1]) - min(box1[3], box2[3])
            h_or_v = "v"
    elif v_overlap > overlap_th * min(box1[3] - box1[1], box2[3] - box2[1]):
        if abs(y1 - y2) < side_center_th:
            dist2 = max(box1[0], box2[0]) - min(box1[2], box2[2])
            h_or_v = "h"

    return min(dist1, dist2), h_or_v


def center_distance(box1, box2):
    # 计算两个bounding box中心点之间的距禿
    x1 = (box1[0] + box1[2]) / 2
    y1 = (box1[1] + box1[3]) / 2
    x2 = (box2[0] + box2[2]) / 2
    y2 = (box2[1] + box2[3]) / 2

    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2), abs(x1 - x2), abs(y1 - y2)


def merge_boxes(box1, box2):
    # 合并两个bounding box
    x1 = min(box1[0], box2[0])
    y1 = min(box1[1], box2[1])
    x2 = max(box1[2], box2[2])
    y2 = max(box1[3], box2[3])
    return [x1, y1, x2, y2]


def post_process_bounding_boxes(
        boxes, iou_th=0.5, iomin_th=0.5, center_dist_th=60, center_dist_ratio_th=0.5,
        box_dist_th=20, side_center_th=30, small_side_th=40, small_area_th=1600, obv_ratio_th=5):

    # while True:
    #     merge_flag = False
    #     merged_boxes = []
    #     while boxes:
    #         box = boxes.pop(0)
    #         for other in boxes:
    #             iou, iomin = box_iou(box, other)
    #             h_dist, v_dist = center_distance(box, other)
    #             box_dist = box_distance(box, other)
    #             small_w = min(box[2] - box[0], other[2] - other[0])
    #             small_h = min(box[3] - box[1], other[3] - other[1])
    #
    #             if iou > iou_th:
    #                 boxes.remove(other)
    #                 box = merge_boxes(box, other)
    #                 merge_flag = True
    #             elif iomin > iomin_th:
    #                 if h_dist < small_w * center_dist_th and v_dist < small_h * center_dist_th:
    #                     boxes.remove(other)
    #                     box = merge_boxes(box, other)
    #                     merge_flag = True
    #             elif box_dist < box_dist_th:
    #                 boxes.remove(other)
    #                 box = merge_boxes(box, other)
    #                 merge_flag = True
    #         merged_boxes.append(box)
    #     boxes = merged_boxes
    #     if not merge_flag:
    #         break

    # 合并IoU大的bounding box
    while True:
        merge_flag = False
        merged_boxes = []
        while boxes:
            box = boxes.pop(0)
            for other in boxes:
                iou, io1, io2 = box_iou(box, other)
                if iou > iou_th:
                    boxes.remove(other)
                    box = merge_boxes(box, other)
                    merge_flag = True
            merged_boxes.append(box)
        boxes = merged_boxes
        if not merge_flag:
            break

    # 合并中心距离小的bounding box
    while True:
        merge_flag = False
        merged_boxes = []
        while boxes:
            box = boxes.pop(0)
            for other in boxes:
                dist, h_dist, v_dist = center_distance(box, other)
                if dist < center_dist_th:
                    boxes.remove(other)
                    box = merge_boxes(box, other)
                    merge_flag = True
            merged_boxes.append(box)
        boxes = merged_boxes
        if not merge_flag:
            break

    # 合并有水平/垂直重叠，且垂直/水平距离小，且其中一个面积小的bounding box
    while True:
        merge_flag = False
        merged_boxes = []
        while boxes:
            box = boxes.pop(0)
            for other in boxes:
                dist, h_or_v = box_distance(box, other, side_center_th=side_center_th)
                min_area = min((box[2] - box[0]) * (box[3] - box[1]), (other[2] - other[0]) * (other[3] - other[1]))
                min_side = min(box[2] - box[0], other[2] - other[0], box[3] - box[1], other[3] - other[1])

                if h_or_v == "h":
                    ratio = (box[2] - box[0]) / (other[2] - other[0])
                else:
                    ratio = (box[3] - box[1]) / (other[3] - other[1])

                if dist < box_dist_th:
                    if min_area < small_area_th or min_side < small_side_th:
                        boxes.remove(other)
                        box = merge_boxes(box, other)
                        merge_flag = True
                    elif ratio > obv_ratio_th or 1 / ratio > obv_ratio_th:
                        boxes.remove(other)
                        box = merge_boxes(box, other)
                        merge_flag = True
            merged_boxes.append(box)
        boxes = merged_boxes
        if not merge_flag:
            break

    # while True:
    #     merge_flag = False
    #     merged_boxes = []
    #     while boxes:
    #         box = boxes.pop(0)
    #         for other in boxes:
    #             iou, iomin = box_iou(box, other)
    #             h_dist, v_dist = center_distance(box, other)
    #             box_dist = box_distance(box, other)
    #             small_w = min(box[2] - box[0], other[2] - other[0])
    #             small_h = min(box[3] - box[1], other[3] - other[1])
    #
    #             if iou > iou_th:
    #                 boxes.remove(other)
    #                 box = merge_boxes(box, other)
    #                 merge_flag = True
    #             elif iomin > iomin_th:
    #                 if h_dist < small_w * center_dist_th and v_dist < small_h * center_dist_th:
    #                     boxes.remove(other)
    #                     box = merge_boxes(box, other)
    #                     merge_flag = True
    #             elif box_dist < box_dist_th:
    #                 boxes.remove(other)
    #                 box = merge_boxes(box, other)
    #                 merge_flag = True
    #         merged_boxes.append(box)
    #     boxes = merged_boxes
    #     if not merge_flag:
    #         break

    # merged = []
    # while boxes:
    #     box = boxes.pop(0)
    #     to_merge = []
    #     for other in boxes:
    #         if overlap(box, other) or box_distance(box, other) < 20:
    #             to_merge.append(other)
    #
    #     for other in to_merge:
    #         boxes.remove(other)
    #         box = merge_boxes(box, other)
    #
    #     merged.append(box)
    #
    # final_merged = []
    # while merged:
    #     box = merged.pop(0)
    #     to_merge = []
    #     for other in merged:
    #         if overlap(box, other) or box_distance(box, other) < 20:
    #             to_merge.append(other)
    #
    #     for other in to_merge:
    #         merged.remove(other)
    #         box = merge_boxes(box, other)
    #
    #     final_merged.append(box)

    return boxes


def is_overlapping(box1, box2):
    # 检查两个 boxes 是否重叠
    return not (box1[2] < box2[0] or box1[0] > box2[2] or box1[3] < box2[1] or box1[1] > box2[3])


def distance(box1, box2):
    # 计算两个 boxes 之间的最近距离
    x_dist = max(0, max(box1[0], box2[0]) - min(box1[2], box2[2]))
    y_dist = max(0, max(box1[1], box2[1]) - min(box1[3], box2[3]))
    return (x_dist ** 2 + y_dist ** 2) ** 0.5


def merge_nearby_boxes(bounding_boxes):
    # 合并最近的两个 boxes
    min_dist = float('inf')
    min_pair = (0, 1)
    for i in range(len(bounding_boxes)):
        for j in range(i + 1, len(bounding_boxes)):
            d = distance(bounding_boxes[i], bounding_boxes[j])
            if d < min_dist:
                min_dist = d
                min_pair = (i, j)

    # 合并 bounding box
    i, j = min_pair
    merged_box = [
        min(bounding_boxes[i][0], bounding_boxes[j][0]),
        min(bounding_boxes[i][1], bounding_boxes[j][1]),
        max(bounding_boxes[i][2], bounding_boxes[j][2]),
        max(bounding_boxes[i][3], bounding_boxes[j][3])
    ]

    # 更新 bounding boxes 列表
    new_bounding_boxes = [bounding_boxes[k] for k in range(len(bounding_boxes)) if k not in min_pair]
    new_bounding_boxes.append(merged_box)

    return new_bounding_boxes


def filter_small_boxes(bounding_boxes, width, height, area_threshold=0.00025, aspect_threshold=0.0025):
    # 过滤掉面积小于阈值的 bounding boxes
    new_bounding_boxes = []
    for box in bounding_boxes:
        x1, y1, x2, y2 = box
        box_width = x2 - x1
        box_height = y2 - y1
        box_area = box_width * box_height
        box_aspect = min(box_width, box_height)

        if box_area > area_threshold * width * height and box_aspect > aspect_threshold * height:
            new_bounding_boxes.append(box)

    return new_bounding_boxes