# 使用官方的miniconda3作为基础镜像
FROM conda/miniconda3

# 设置工作目录
WORKDIR /app

# 配置conda环境
RUN conda create -n text python=3.8 && \
    echo "source activate text" > ~/.bashrc && \
    /bin/bash -c "source activate text && \
    conda install -y pytorch==1.8.0 torchvision==0.9.0 torchaudio==0.8.0 cpuonly -c pytorch && \
    pip install tqdm==4.65.0 -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    conda install -y tensorboardX && \
    pip install jieba -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install boto3 -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install regex==2022.10.31 -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install scikit-learn   && \
    pip install flask==2.2.3 "


# 将项目文件复制到工作目录
COPY . /app
# 暴露Flask应用所需的端口
EXPOSE 5000
# 开启flask服务
CMD python test.py
