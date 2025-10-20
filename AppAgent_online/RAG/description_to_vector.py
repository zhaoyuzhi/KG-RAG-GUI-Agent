import os
import csv
import numpy as np
from openai import OpenAI
from pinecone import Pinecone

OPENAI_API_KEY = "sk-......"
PINECONE_API_KEY = "......"

def normalize_l2(x):
    x = np.array(x)
    if x.ndim == 1:
        norm = np.linalg.norm(x)
        if norm == 0:
            return x
        return x / norm
    else:
        norm = np.linalg.norm(x, 2, axis=1, keepdims=True)
        return np.where(norm == 0, x, x / norm)

def get_embedding(text, model="text-embedding-3-large", dim=512):
    text = text.replace("\n", " ")
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(
       model=model, input=[text], encoding_format="float"
    )
    cut_dim = response.data[0].embedding[:dim]
    norm_dim = normalize_l2(cut_dim)

    return norm_dim
   # return client.embeddings.create(input=[text], model=model).data[0].embedding

def save_embeddings(description_dir, save_path):
    description_list = os.listdir(description_dir)
    description_list.sort()
    description_list = [d for d in description_list if d.endswith('.txt')]
    all_embeddings = []
    for i, filename in enumerate(description_list):
        print(filename, f', {i + 1}/{len(description_list)}')
        with open(os.path.join(description_dir, filename), "r", encoding='utf-8') as f:
            text = f.read()
            per_embedding = get_embedding(text, dim=512)
            all_embeddings.append({
                "id": filename,
                "values": list(per_embedding)
            })
    with open(save_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'values'])
        for embedding in all_embeddings:
            writer.writerow([embedding['id'], embedding['values']])

def pinecone_upsert_embeddings(description_dir, namespace, index_name="screenshot-description"):
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(index_name)

    description_list = os.listdir(description_dir)
    description_list.sort()
    description_list = [d for d in description_list if d.endswith('.txt')]
    for filename in description_list:
        print(filename)
        with open(os.path.join(description_dir, filename), "r", encoding='utf-8') as f:
            text = f.read()
            per_embedding = get_embedding(text, dim=512)
            index.upsert(
                vectors=[
                    {
                        "id": filename,
                        "values": list(per_embedding)
                    }
                ],
                namespace=namespace
            )

def pinecone_get_candidates(description, namespace, index_name="screenshot-description"):
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(index_name)
    embedding = get_embedding(description, dim=512)
    response = index.query(vector=list(embedding), namespace=namespace, top_k=5, include_values=False)['matches']
    return response

def get_candidates(description, all_embeddings_path):
    # 读取csv文件中的所有embedding
    with open(all_embeddings_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        all_embeddings = []
        for row in reader:
            all_embeddings.append({
                "id": row[0],
                "values": np.array(eval(row[1]))
            })
    query_embedding = get_embedding(description, dim=512)
    # 计算查询embedding与所有embedding的余弦相似度
    similarities = []
    for embedding in all_embeddings:
        similarity = np.dot(query_embedding, embedding['values'])
        similarities.append({
            "id": embedding['id'],
            "similarity": similarity
        })
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    return similarities

# # description_dir = r'/Users/jinpeng/Desktop/text'
# # save_path = r'/Users/jinpeng/Desktop/text/descriptions_embeddings.csv'
# description_dir = r'E:\Datasets\AppTestAgent\0624HuaweiMusic\all_nodes\descriptions'
# save_path = r'E:\Datasets\AppTestAgent\0624HuaweiMusic\all_nodes\descriptions_embeddings.csv'
# # namespace = "HuaweiMusic"
# save_embeddings(description_dir, save_path)

# description = """应用类型：音乐类应用
# 页面性质：推荐页面
# 页面布局：
#   * 顶部导航栏：包含多个分类标签，如推荐、乐馆、听书、儿童、会员等。
#   * 搜索栏：位于导航栏下方，提供搜索功能。
#   * 用户信息区：显示用户头像和等级信息。
#   * 推荐内容区：展示推荐的音乐内容，包括专辑封面、歌曲名称和歌手信息。
#   * 播放控制区：包含播放按钮和其他播放控制选项。
#   * 底部导航栏：包含首页、直播、雷达、社区和我的等功能按钮。
# 页面功能：
#   * 分类切换：用户可以通过点击顶部导航栏的标签切换不同的内容分类。
#   * 搜索功能：用户可以通过搜索栏搜索特定的音乐内容。
#   * 查看用户信息：用户可以查看自己的头像和等级信息。
#   * 播放推荐音乐：用户可以点击推荐内容区的播放按钮播放推荐的音乐。
#   * 底部导航：用户可以通过底部导航栏切换到首页、直播、雷达、社区和我的页面。"""
# all_embedding_path = r'/Users/jinpeng/Desktop/text/descriptions_embeddings.csv'
# # matches = get_candidates(description)
# matches = get_candidates(description, all_embedding_path)
