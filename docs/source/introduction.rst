Introduction
============

What Is NofearDB?
-----------------

NofearDB is a database management system (DBMS) that holds and manages relational data in a document oriented database. Without using SQL it provides a rich ORM toolset for CRUD operations.

Why another database system?
----------------------------

Given the number of existing database systems, this question can indeed arise. First and foremost, NofearDB is about being able to store complex data with as little effort as possible. To this end, NofearDB concentrates only on the essentials: data can be stored, changed and read and simple relations can be mapped. There is no need to set up a server or define a complex database schema. It is sufficient to define documents and a path where the database is to be stored. A database can be set up with just a few lines of code. The fact that the data is stored in the form of JSON objects has several advantages: First of all, the database remains human-readable. This can help to solve problems manually or to look up certain facts. In addition, the database is less prone to errors. A single faulty data record does not immediately render the entire database unusable. Last but not least, the problem of concurrency is minimized. With conventional SQL databases, all read and write accesses access the same database file. This results in faster locks than if individual json files are processed independently of each other.

The serverless architecture not only offers the advantage of lower administration costs. Thanks to this architecture, databases can function on any file system, whether local or on cloud storage. Any user with access to the storage can simply connect to the database. This makes a NofearDB database very easy to back up and transport. Other embedded databases such as SQLite also enjoy these advantages, but these systems are usually very susceptible to errors with concurrent accesses. NofearDB was designed from the outset with the idea in mind that there could be competing accesses. Therefore, various mechanisms were built in to minimize the risk of parallel accesses.

Who is NofearDB for?
--------------------

All these advantages come at a price: NofearDB causes a large number of file system accesses. Since reading and writing from a file system is a very slow operation, NofearDB can never achieve the performance of a conventional database system. Many optimizations have been built in to make reading from the database as performant as possible, but NofearDB is still more suitable for smaller amounts of data. Good results have been achieved for several thousand data records, but the time required for read and write operations increases significantly for many entries.

Who is NofearDB not for?
-------------------------

NofearDB is not 100% ACID compliant. Therefore the use of NofearDB is not recommended for cirtical data or systems, that need to make sure the data they work on is always in an absolutly correct state. Also NofearDB does not support immutable data at the moment.