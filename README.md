Load MD files from Elastic Path Docs site in a MongoDB Atlas Cluster

### How to get Started?


* Install the required dependencies:
```bash
python -m venv myenv
source myenv/bin/activate
python -m pip install -r requirements.txt   


deactivate
```

* Load VectorDB using the PDFs in the data directory
```bash
usage: populate_database.py [-h] [--url URL] [--md] [--pdf] [--data_path DATA_PATH] [--reset] [--vectordb_path VECTORDB_PATH]

optional arguments:
  -h, --help                show this help message and exit
  --url URL                 The URL to process
  --md                      Process the MD files in the data directory.
  --pdf                     Process the PDFs in the data directory.
  --data_path DATA_PATH     The path to the data directory.
  --reset                   Reset the database.
  --vectordb_path VECTORDB_PATH
                            The path to the vector database.
  --chunk_size              Size of the Chunks
```
Use the flag ```--reset``` to clear the database


I would like to create a product for jeans with length and waist size as variations. 
Give me all the steps to do that and some sample data to do this  in Commerce Manager

How do I create a 20% discount promotion for cart that contains shoes over $100

How do I create a bundle that contains 1 sofa with 3 variations and an optional ottoman with 2 variations

Can I search a custom api field

how do I create a monthly subscription for a shampoo and apply a 5% discount for the first 3 months

```bash
python populate_database.py --reset --vectordb_path chroma_md --md --data_path ./data_md/docs/commerce-manager --chunk_size 2000 
python populate_database.py --vectordb_path chroma_md --md --data_path ./data_md/guides --chunk_size 2000 
```
- 

## Credit
A lot of this code comes from https://www.youtube.com/watch?v=2TJxpyO3ei4 
