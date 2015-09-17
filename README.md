# Centrice
Mirror Domain Distribution Central Service


## API

<pre>
1.  GET site domains by rank and status
    GET /domains/$site/?status=up&rank=0
      Params:
        site: The site id, required
        status: The accessible status, default is up,i.e. not blocked.
                Enum(up|down|all)
        rank: The domain rank, default is 0, i.e. public. use rank=all to get all domains
        format: The output format, default is 'plain', means output plain text, domains seperated by line feed
                Enum(plain|json|detail)
                  Format 'detail' will output each JSON with each domain's detail information:
                  [{domain:"up.a.com",blocked:true,rank:1}]


    Output:
      Domain list seperated by line feed char or JSON


2.  POST /domains/$site/
    POST /domains/$site/
    Body:up=a.example.com,b.example.com&down=x.example.com
    Params:
      site: The site ID
      up: up domain split by comma or space
      down: down domain split by comma or space
</pre>

### Installation
Clone this repository.
```bash
cd src;
pip install -r requirements.txt;
touch  settings_local.py;
python app.py;
```
