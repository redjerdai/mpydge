# mpydge

# Data

##General concepts
Basic instrument for data guidance -- `pandas.DataFrame`. 
If you want to use some data, read it at first with `pandas`.

It is convenient to separate data onto two basic types: categorical and numerical
(we do not support ordered categories yet, sorry) and thus we do. 
Currently `pandas` supports wide variety of data types, but for the package's
computations you have to set all needed fields' data types to these two:
* `'category'` (so that data is treated as categorical)
* `'float64'` (so that data is trated as numerical)

All other data types will be ignored. You can assess what data type column has
in the following way: `print(data['column'].dtype.name`. 

For example, the following `'column1'` will be correctly treated as categorical:

```buildoutcfg
>>> a = ... # a pandas.DataFrame instance
>>> print(a['column1'].dtype.name)
'category'
```

On the contrary, the following `'column2'` is not treated as numerical correctly
```buildoutcfg
>>> a = ... # a pandas.DataFrame instance
>>> print(a['column2'].dtype.name)
'int64'
```

## Out data format
We use a special class to hold all components of data sets, including:
* train sample
* validation sample
* test sample

Each of them contains of:
* categorical fields
* numerical fields
* output field (could be either categorical or numerical)

It is a convention for us to initialise data with `Conductor` data class

```
class Conductor(data_frame, target, 
                embedding_strategy='default', embedding_explicit=None):
                """
                data_frame            a pandas.DataFrame instance to use
                target                a string = name of the target field
                embedding_strategy    a strategy describing how to embed categorical fields
                                      'default' uses special rule of thumb to embed fields
                                      could be set to None (needs embedding_explicit to be defined)
                embedding_explicit    if embedding_strategy is None, uses explicitly defined embedding dimensions
                """
```

After initialisation all data is available in the described formerly way through data field:

```
import pandas
from mpydge.data_keeper.keeper import Conductor

d = './my_data_set.csv'
data_frame = pandas.read_csv(d)
data_hub = Conductor(data_frame=data_frame, target='my_target_column')

data_hub.data.train               # here lies all train data
data_hub.data.validation          # here lies all validation data
data_hub.data.test                # here lies all test data

# for example, let's take a look at train data
data_hub.data.train.categorical   # here lies categorical train data
data_hub.data.train.numerical     # here lies numerical train data
data_hub.data.trin.output         # here lies output (=target) train data
```
