## 文本分类服务报告

### 服务搭建

```bash
#拉取镜像
docker pull registry.cn-wulanchabu.aliyuncs.com/ndd/textreview:v3.1

#创建容器后台守护进程
docker run -it -d --name textreview0 -p 5001:5000  registry.cn-wulanchabu.aliyuncs.com/ndd/textreview:v3.1

docker run -it -d -p 5001:5000 registry.cn-wulanchabu.aliyuncs.com/ndd/textreview:v3.1
```

### 服务使用

```bash
#web页面
http://flaskip:5000/static/predict.html
```

```python
#远程发包，input.txt中存放需要预测的文本,output.txt中存放预测结果
import requests
import json

url = "http://flaskip:5000/predict"
url1= "http:/flaskip:5000/switchlevel"
def send_swithlevel(level):
    data = {"level": level}
    response = requests.post(url1, json=data)
    if response.status_code == 200:
        result = response.json()
        print(result)
    else:
        print("请求失败")

def send_single_text(text):
    response = requests.post(url, json={'text': text})

    if response.status_code == 200:
        result = response.json()
        print(result)
    else:
        print("请求失败")


def send_text_file(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    results = []
    for line in lines:
        line = line.strip()
        response = requests.post(url, json={'text': line})

        if response.status_code == 200:
            result = response.json()
            # print(result)
            results.append(f"{result['category']}\n")
        else:
            print(f"请求失败: {line}")

    with open(output_file, "w", encoding="utf-8") as f:
        # print(results)
        f.writelines(results)


if __name__ == "__main__":
    #更改审核等级 2:严格审核 1.正常审核 0.仅分类
    send_swithlevel(2)
    # 发送单句文本
    # send_single_text("青春的羞涩和肆意的放纵，在色彩斑斓的夜晚交织")
    # 从本地文件发送文本
    # send_text_file("input.txt", "output.txt")
```

### 项目说明

```
本项目基于bert+cnn实现了对中文文本的分类，可以将文本分为色情、政治和其他。
可以通过send_swithlevel函数来发送切换版本请求，服务默认开启严格审核模式。（2:严格审核 1.正常审核 0.仅分类）
```

#### 效果总结&Case说明

##### 语料比说明

模型采用的数据集由三部分合成:

```
THUCNews中文文本分类数据集
第三方色情数据集 
Jigsaw毒性分类数据集
```

| 数据集 | 数据量 |
| ------ | ------ |
| 训练集 | 3.2w   |
| 验证集 | 4k     |
| 测试集 | 4k     |

```
THUCNews: 从政治抽取1w数据，从金融，教育，运动，游戏，娱乐各自抽取1k数据组成正常类别    8:1:1
Jigsaw毒性分类:从色情抽取6k数据，从其他类别共抽取6k数据      10:1:1
第三方色情数据集：抽取4k色情数据和4k非色情数据           6:1:1
训练集:8K政治、8K色情、1.6w正常
验证集:1k政治、1k色情、2k正常
测试集:1k政治、1k色情、2k正常
```

##### 测试结果

###### 测试集

| 文本分类 |           |        |          |
| -------- | --------- | ------ | -------- |
| 种类     | Precision | Recall | F1 Score |
| 其他     | 94.84%    | 91.69% | 93.24%   |
| 政治     | 96.73%    | 97.50% | 97.11%   |
| 色情     | 87.01%    | 92.08% | 89.47%   |

###### 在Jigsaw毒性数据与第三方色情数据的测试集测试

| 第三方色情数据集 |           |        |          |
| ---------------- | --------- | ------ | -------- |
| 种类             | Precision | Recall | F1 Score |
| 其他             | 95.51%    | 89.78% | 92.55%   |
| 色情             | 90.76%    | 95.26% | 92.95%   |

| Jigsaw毒性分类 |           |        |          |
| -------------- | --------- | ------ | -------- |
| 种类           | Precision | Recall | F1 Score |
| 其他           | 84.65%    | 82.19% | 83.40%   |
| 色情           | 83.03%    | 84.23% | 83.63%   |

##### Case说明

###### 测试用例

```
青春的羞涩和肆意的放纵，在色彩斑斓的夜晚交织
改革春风吹满地
半场战报,沙特暂领先阿根廷
若要人不知，除非己莫为
苟利国家生死以，岂因祸福趋避之
狠狠的插入，撞击花心
```

##### web界面

<img src=".\pictures\web.png" style="zoom: 45%;" />

