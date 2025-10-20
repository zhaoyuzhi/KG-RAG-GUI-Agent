import json
import csv

# 读取 JSON 文件
def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data

# 从 JSON 中提取信息并保存到 CSV
def extract_metadata_to_csv(json_file, output_csv):
    # 读取 JSON 数据
    data = read_json(json_file)

    # 打开 CSV 文件进行写入
    with open(output_csv, mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['Node ID', 'Image', 'Image JSON']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        # 写入 CSV 头
        writer.writeheader()

        # 遍历每个节点
        for node_id, node_data in data.get('nodes', {}).items():
            # 遍历 exactScenes
            for scene in node_data.get('exactScenes', []):
                image = scene.get('img')
                image_json = scene.get('img').replace('.jpeg', '.json')  # 假设 JSON 文件名与图片文件名一致

                # 将信息写入 CSV
                writer.writerow({'Node ID': node_id, 'Image': image, 'Image JSON': image_json})

    print(f"Metadata has been saved to {output_csv}")

# 示例使用
package_names = ['com.ctrip.harmonynext', 'com.dragon.read.next', 'com.netease.cloudmusic.hm', 'com.tencent.hm.qqmusic', 'com.sina.weibo.stage', 'com.vip.hosapp']
#package_names = ['com.gotokeep.keep'] #['com.alipay.mobile.client']
graph_dir = "/home/app_agent/RAGGeneration_New/data/oracle_test_app_second_stage/"

for name in package_names:
        
    json_file = f'{graph_dir}/{name}/graph/{name}.json'  # 输入的 JSON 文件路径
    output_csv = f'{graph_dir}/{name}/graph/metadata.csv'  # 输出的 CSV 文件路径

    extract_metadata_to_csv(json_file, output_csv)
