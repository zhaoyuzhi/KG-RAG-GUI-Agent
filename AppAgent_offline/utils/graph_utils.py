import pandas as pd

def get_metadata(data):
    metadata_list = []
    node_data = data["nodes"]
    for sid, node in node_data.items():
        metadata = node["exactScenes"][0]
        img_path = metadata["img"]
        layout_path = metadata["layout"]
        metadata_list.append([sid, img_path, layout_path])
    my_df = pd.DataFrame(metadata_list)
    my_df.to_csv('dist/static/metadata.csv', index=False, header=False)
    #my_df.to_csv('dist/static/metadata.csv', index=False, header=False)
