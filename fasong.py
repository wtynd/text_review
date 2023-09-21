import requests

# 测试基本功能
data = {"text": "青春的羞涩和肆意的放纵，在色彩斑斓的夜晚交织"}
response = requests.post("http://8.139.4.139:5001/predict", json=data)
print("测试基本功能:")
print(response.json())

# 测试包含敏感词的情况
data = {"text": "习近平"}
response = requests.post("http://8.139.4.139:5001/predict", json=data)
print("测试包含敏感词的情况:")
print(response.json())

# 测试添加键值对
data = {"type": "测试类型", "text": "测试添加", "operation": "add"}
response = requests.post("http://8.139.4.139:5001/update_key_value", json=data)
print("测试添加键值对:")
print(response.json())

# 测试包含新增敏感词的情况
data = {"text": "这是一个测试添加"}
response = requests.post("http://8.139.4.139:5001/predict", json=data)
print("测试包含新增敏感词的情况:")
print(response.json())

# 测试查询键值对
data = {"text": "测试"}
response = requests.post("http://8.139.4.139:5001/query_key_value", json=data)
print("测试查询键值对:")
print(response.json())

# 测试删除键值对
data = {"type": "测试类型", "text": "测试添加", "operation": "delete"}
response = requests.post("http://8.139.4.139:5001/update_key_value", json=data)
print("测试删除键值对:")
print(response.json())

# 测试包含已删除敏感词的情况
data = {"text": "这是一个测试添加"}
response = requests.post("http://8.139.4.139:5001/predict", json=data)
print("测试包含已删除敏感词的情况:")
print(response.json())

# 测试查询不存在的键值对
data = {"text": "不存在的值"}
response = requests.post("http://8.139.4.139:5001/query_key_value", json=data)
print("测试查询不存在的键值对:")
print(response.json())