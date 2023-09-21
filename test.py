import os
from flask import Flask, jsonify, request
import sqlite3
from sqlite3 import Error
import io
import json
import argparse
import jieba
import torch
import torch.nn as nn
import torch.nn.functional as F
from pytorch_pretrained import BertModel, BertTokenizer
app = Flask(__name__)
key = {0: '其他',
       1: '政治',
       2: '色情',
       }

dataset = 'THUCNews'
jieba.load_userdict('./THUCNews/data1/jieba_buchong.txt')
stopwords_path='./THUCNews/data1/stopwords.txt'
class Config(object):
    def __init__(self):
        self.sensitive_words = self.load_sensitive_words("./THUCNews/data1/my_database.db")
        self.model_name = 'bert'
        self.class_list = [str(i) for i in range(len(key))]  # 类别名单
        self.save_path = dataset + '/saved_dict/bert.ckpt'        # 模型训练结果
        # self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')   # 设备
        self.device = torch.device('cpu')
        self.require_improvement = 1000                                 # 若超过1000batch效果还没提升，则提前结束训练
        self.num_classes = len(self.class_list)                         # 类别数
        self.bert_path = './bert_pretrain'
        self.tokenizer = BertTokenizer.from_pretrained(self.bert_path)
        self.hidden_size = 768
        self.filter_sizes = (2, 2, 2)                                   # 卷积核尺寸
        self.num_filters = 256                                          # 卷积核数量(channels数)
        self.dropout = 0.1

    def build_dataset(self, text):
        lin = text.strip()
        max_length = 20  # 或者其他您想要的最大长度
        token = self.tokenizer.tokenize(lin)[:max_length - 2]
        token = ['[CLS]'] + token + ['[SEP]']
        token_ids = self.tokenizer.convert_tokens_to_ids(token)
        input_ids = token_ids + [0] * (max_length - len(token_ids))
        mask = [1] * len(token_ids) + [0] * (max_length - len(token_ids))
        return torch.tensor([input_ids], dtype=torch.long), torch.tensor([mask])

    def load_sensitive_words(self, db_file):
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM key_value_pairs")
        rows = cursor.fetchall()
        sensitive_words = {}
        for row in rows:
            sensitive_words[row[1]] = row[0]
        return sensitive_words

class Model(nn.Module):

    def __init__(self, config):
        super(Model, self).__init__()
        self.bert = BertModel.from_pretrained(config.bert_path)
        for param in self.bert.parameters():
            param.requires_grad = True
        self.convs = nn.ModuleList(
            [nn.Conv2d(1, config.num_filters, (k, config.hidden_size)) for k in config.filter_sizes])
        self.dropout = nn.Dropout(config.dropout)

        self.fc_cnn = nn.Linear(config.num_filters * len(config.filter_sizes), config.num_classes)

    def conv_and_pool(self, x, conv):
        x = F.relu(conv(x)).squeeze(3)
        x = F.max_pool1d(x, x.size(2)).squeeze(2)
        return x

    def forward(self, x):
        context = x[0]  # 输入的句子
        mask = x[1]  # 对padding部分进行mask，和句子一个size，padding部分用0表示，如：[1, 1, 1, 1, 0, 0]
        encoder_out, text_cls = self.bert(context, attention_mask=mask, output_all_encoded_layers=False)
        out = encoder_out.unsqueeze(1)
        out = torch.cat([self.conv_and_pool(out, conv) for conv in self.convs], 1)
        out = self.dropout(out)
        out = self.fc_cnn(out)
        return out

config = Config()
model = Model(config).to(config.device)
model.load_state_dict(torch.load(config.save_path, map_location='cpu'))
model.eval()
stopwords = set()
with open(stopwords_path, 'r', encoding='utf-8') as f:
    for line in f:
        stopwords.add(line.strip())

def prediction_model(text):
    """输入一句问话预测"""
    words = jieba.lcut(text)
    for sensitive_word in config.sensitive_words:
        if sensitive_word in text:
            return text, config.sensitive_words[sensitive_word]


    words = [w for w in words if w not in stopwords]
    new_text = ' '.join(words)

    data = config.build_dataset(new_text)
    with torch.no_grad():
        outputs = model(data)

        if outputs.max() < 0.6:
            num = 0
        else:
            num = torch.argmax(outputs)
    return text, key[int(num)]

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json(force=True)
    text = data['text']

    lines = text.splitlines()
    predictions = []
    for line in lines:
        original_text, prediction = prediction_model(line)
        result_line = f"{prediction}"
        predictions.append(result_line)
    result = '\n'.join(predictions)
    return jsonify(result)

@app.route('/update_key_value', methods=['POST'])
def update_key_value():
    data = request.get_json()
    key = data.get('type')
    value = data.get('text')
    operation = data.get('operation')

    if not key or not value or not operation:
        return jsonify({"error": "Missing required parameters: type, text, operation."}), 400

    conn = sqlite3.connect("./THUCNews/data1/my_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM key_value_pairs WHERE value=?", (value,))
    row = cursor.fetchone()

    if operation == "add":
        if row:
            cursor.execute("UPDATE key_value_pairs SET key=? WHERE value=?", (key, value))
            conn.commit()
            message = f"已覆盖{value}"
        else:
            cursor.execute("INSERT INTO key_value_pairs (key, value) VALUES (?, ?)", (key, value))
            conn.commit()
            message = f"已新增{value}"
    elif operation == "delete":
        if row:
            cursor.execute("DELETE FROM key_value_pairs WHERE value=?", (value,))
            conn.commit()
            message = f"已删除{value}"
        else:
            message = f"不存在{value}"
    else:
        return jsonify({"error": "Invalid operation, it must be 'add' or 'delete'."}), 400

    conn.close()
    config.sensitive_words = config.load_sensitive_words("./THUCNews/data1/my_database.db")
    print(message)
    return jsonify({"message": message}), 200

@app.route('/query_key_value', methods=['POST'])
def query_key_value():
    data = request.get_json()
    value = data.get('text')

    if not value:
        return jsonify({"error": "Missing required parameter: text."}), 400

    conn = sqlite3.connect("./THUCNews/data1/my_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM key_value_pairs WHERE value LIKE ?", (f"%{value}%",))
    rows = cursor.fetchall()

    key_value_pairs = []
    for row in rows:
        key_value_pairs.append({"key": row[0], "value": row[1]})

    conn.close()
    return jsonify({"result": key_value_pairs}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)