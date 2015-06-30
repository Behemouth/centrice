# Centrice
Mirror Domain Distribution Central Service


## API

<pre>
1. GET site domains by rank and status
      GET /domains/$site/?status=up&rank=0   or RESTful
      GET /domains/$site/up
      Params:
        site: The site id, required
        status: The accessible status, default is up,i.e. not blocked.
                Enum(up|down)
        rank: The domain rank, default is 0, i.e. public, higher rank requires higher authority.
        format: The output format, default is 'plain', means output plain text, domains seperated by line feed
              Enum(plain|json)

      Output:
        Domain list seperated by line feed char


2. POST /domains/$site/
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
