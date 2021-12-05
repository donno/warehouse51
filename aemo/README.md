aemo
====
AEMO is the Australian Energy Market Operator and are responsible for the
National Electricity Market (NEM). They make their data available to increase
public understanding and promote transparency.

https://visualisations.aemo.com.au/aemo/nemweb/index.html

What it does
------------
The script processes the CSV files from NEMWeb and constructs are single
parquet file with the results for the given dataset.

To date the only data that has been tested is archived rooftop photovoltaic
actuals.

The script is also set-up to generate matplotlib figures of the data.

Known issue
-----------
The version that attempts to write out an Apache Parquet file using the schema
dervied from the YAML fails to capture date times properly. They end up coming
out as dates. Prior to upgrading from pyarrow-2.0.0 to 6.0.1 it would always
say pyarrow.lib.ArrowInvalid: Timestamp value had non-zero intraday
milliseconds when creating the pyarrow array, which as I typed this up I
might really mean the same as non-zero seconds between days. Something to
consider next time I look at that.

Authors
---------
 * Sean Donnellan <darkdonno@gmail.com>

License
---------------------
The following applies to the Python scripts and not the YAML configuration
files unless stated otherwise.

The MIT License (see LICENSE.txt or here for convenience)

Copyright (c) 2021 Sean Donnellan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
