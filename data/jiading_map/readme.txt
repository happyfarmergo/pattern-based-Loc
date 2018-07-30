原始ID编码文件：
1. Nodes.csv 所有节点
2. highway.csv 所有切割后的路段 ['id','oneway','category','nodes']

改变编码ID后的文件
1. Edges.csv 多了三个字段 ['id','from','to','cost','nodes']
2. WA_Edges.csv from to 重新编码 ['id','from','to','cost']
