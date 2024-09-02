# NofearDB

Welcome to NofearDB, the NoSQL database system without the headache.

NOFEAR stands for:

- **No**SQL: NofearDB is document based and relies on json.
- **F**ast: NofearDB is designed for good performance despite many read and write accesses on the filesystem.
- **E**mbedded: NofearDB does not require to run a database server.
- **A**nd: Thats not all!
- **R**eliable: Despite its simplicity and design, NofearDB enables stable data storage, even with concurrent access in multi-user environments.

NofearDB combines the simplicity and flexibility of NoSQL databases like MongDB with schema based approaches of relational databases like MySQL. Therefore you get a handy ORM workflow but with json documents instead of database tables. Because there is no need for a database server and fixed schema tables, every database and every document is self contained, easily backupable and very insusceptible to programming and user errors. This makes NofearDB a perfect fit for small and medium sized applications, where relational data is to be persisted without much effort.

## Features

- Combines the best of both worlds: Relational and NoSQL Database.
- Full Object-Relational-Mapping.
- Simple and with minimal setup requirements. No database Server is needed.
- Works with concurrent read and write operations.
- High performance for small datasets (up to a few thousand entities).
- Dependency free.
- 100% test coverage.

## Documentation

The full documentation can be found here: https://no-fear-db.readthedocs.io

## Disclaimer

Even though NofearDB is designed to work with concurrency, a serverless database system can never be as secure as a conventional system. Every effort has been made to manage concurrent read and write accesses, but the risk of problems occurring can only be reduced to a minimum. There is no guarantee that problems with concurrent accesses are 100% excluded. It is therefore not recommended to use NofearDB in multi-user environments for critical data.

NofearDB is in an early beta stage. Despite sufficient testing, there is no guarantee that it is error-free. The use of NofearDB is at your own risk. In the event of damage, no liability is assumed by the developers or the author.

## Contributing

Whether reporting bugs, discussing improvements and new ideas or writing extensions: Contributions to NofearDB are welcome! Here's how to get started:

1. Check for open issues or open a fresh issue to start a discussion around a feature idea or a bug.
2. Fork the repository on Github, create a new branch off the master branch and start making your changes (known as GitHub Flow).
3. Write a test which shows that the bug was fixed or that the feature works as expected.
4. Send a pull request and bug the maintainer until it gets merged and published.