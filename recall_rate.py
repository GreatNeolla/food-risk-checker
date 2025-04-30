import json
import pprint

# 1. 打开并读取 JSON 文件
with open("/Users/liangnan/Desktop/APAN 5400/Project/food_recall_clean.json", "r") as f:
    recall_data = json.load(f)

# 2. 打印总条数
print(f"Total records: {len(recall_data)}")

# 3. 用 pprint 更漂亮地打印前几条
pprint.pprint(recall_data[:5])

# 4. 如果想看所有字段
