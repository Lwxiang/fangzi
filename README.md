# FangZi

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
    result = True; raise(result)
else:
    result = False; raise(result)
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
