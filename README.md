# Final Blockchain Project

This document provides the instructions for setting up and running the Final Blockchain Project application on Windows and macOS.

## Prerequisites

Before you begin, ensure you have Python installed on your system. The application has been tested on Python 3.7 and above.

## Setup

### Windows

1. Open the Command Prompt.
2. Navigate to the project directory.
3. Create a virtual environment:

    ```shell
    python -m venv venv
    ```

4. Activate the virtual environment:

    ```shell
    .\venv\Scripts\activate
    ```

5. Install the required packages:

    ```shell
    pip install -r requirements.txt
    ```

### macOS and Linux

1. Open the Terminal.
2. Navigate to the project directory.
3. Create a virtual environment:

    ```shell
    python3 -m venv venv
    ```

4. Activate the virtual environment:

    ```shell
    source venv/bin/activate
    ```

5. Install the required packages:

    ```shell
    pip install -r requirements.txt
    ```

## Run the Application

To run the application, execute the following command:

```shell
python src/goodchain.py
```


## P2P Networking on the same network

When starting the app, the ip of your laptop is added to the node_list file in the data file.
This ip is also send to all other nodes. 
So if 2 laptops are using the P2P app, you have to check that in the node_list file you still have the 2 correct ip's.
If not the app will not work well.

Example of node_list file for 2 laptops connected to the same network:

```
["172.20.10.2", "172.20.10.3"]
```
