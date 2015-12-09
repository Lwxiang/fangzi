# FangZi

## Quickly Start
Console

```python setup.py install```

Python Console
```python
from fangzi import FangZi
handler = FangZi()
```

Or use it like a script

```python setup.py --status```

---

### What is FangZi
```FangZi``` is a simple tool for manage functions in ```MongoDB```.

### Dynamic Function Check

Consider this case:
```python
# A data need many check
if rule1_check(data) and rule2_check(data1, data2) and ...:
    # Yes it pass all the rule we made
    # Then we can do the formal process
    ...
```
If we have something need so many rule-check in our project, and those functions of rules many be changed or updated frequently.

It is hard to manage then.

Now here is another way:
```python
flag = True
for func in all_funcs:
    try:
        exec func.code
    except Exception, result:
        flag = result
        
if flag:
    # It pass all the rule we made and let's talk bussiness
```
See, we make the check part invariant.

If we want to manage the functions, all we need is to handle the content of ```func```.

So that we get a dynamic-function-check solution.

### How it works?
The point is that we store all of our check-functions into ```MongoDB```, each function take one Ducument.

We don't need the functions' head and its return, we parse them and make it into the code we need.

Source Function
```python
def check(*args, **kwargs):
    # ... do something
    if valid:
        return True
    else:
        return False
```

Parse Code We Need
```python
# ... do something
if valid:
    result = True; raise Exception(result)
else:
    result = False; raise Exception(result)
```
This code can be execute by ```exec``` and the result will be catch by except.

So we get a full solution for the dynamic-function-check.

### Usage
Install MongoDB: ```pip install -r requirement.txt```

Make sure your local MongoDB server is running

Config the settings in ```settings.py```

Parse from files and launch into database: ```python fangzi.py -p -l```

![img](https://github.com/Lwxiang/fangzi/raw/master/examples/images/parse_and_launch.jpg)

Show the functions' status in database: ```python fangzi.py -s```

![img](https://github.com/Lwxiang/fangzi/raw/master/examples/images/status.jpg)

Wake up the functions by Flag/Group/Name: ```python fangzi.py --wake --flag CODE```

![img](https://github.com/Lwxiang/fangzi/raw/master/examples/images/wake.jpg)

![img](https://github.com/Lwxiang/fangzi/raw/master/examples/images/close.jpg)

### More
A full example is provided in ```example/```

Hope you come to discuss about the solution and any criticism or suggestion is welcome:)

# 中文介绍

### 什么是房子
房子(FangZi)是一个简单的脚本工具，确切的说是一个工具类，可以在你的代码中直接```import```嵌入使用。

### 动态规则检查

看看这个例子：
```python
# A data need many check
if rule1_check(data) and rule2_check(data1, data2) and ...:
    # Yes it pass all the rule we made
    # Then we can do the formal process
    ...
```
当某些数据需要接受大量函数检测时（如合法性检测、特征值封禁、日志分类统计、流水线加工），我们要花费大量的代价去维护一系列函数。

特别当某些检查特征的函数需要经常变动时，当对某些函数进行更改或者添加删除时，这种方式的工作量很大，不易于管理。

现在看看另一个例子：
```python
flag = True
for func in all_funcs:
    try:
        exec func.code
    except Exception, result:
        flag = result
        
if flag:
    # It pass all the rule we made and let's talk bussiness
```
我们把所有的函数一并放在了```all_funcs```里，这样把检测部分的代码固定住了，当我们对函数进行管理时，只需要对func.code进行管理就可以了。

因此我们得到了一个解决方案：

将所有的函数储存在数据库中，并在数据库中通过数据库读写来进行动态管理

当需要使用时，从数据库中取出来，使用```exec```执行其代码部分

### 怎么做
房子(FangZi)是用来把普通的包含函数的源文件转化并写入数据库中的工具，并且提供了管理的方法。

我们使用```MongoDB```进行储存，一个函数(function)对应一个数据库中的文档(Document)

那么怎么用呢？

源函数
```python
def check(*args, **kwargs):
    # ... do something
    if valid:
        return True
    else:
        return False
```

转化后的函数
```python
# ... do something
if valid:
    result = True; raise Exception(result)
else:
    result = False; raise Exception(result)
```

我们将函数中所有的```return Bool```替换为了```result = Bool; raise Exception(result)```，并在使用的时候用```try-except```和```exec```去执行+捕捉。

这样就获得了函数执行的结果。

### 使用
见上文 Usage
