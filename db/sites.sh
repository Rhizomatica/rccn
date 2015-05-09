#"!/bin/bash
# Populate sites in riak

# Talea
curl -v -X PUT http://localhost:8098/buckets/sites/keys/688201 -H "Content-Type: application/json" -d '{"site_name": "Talea", "postcode": "68820", "pbxcode": "1", "network_name": "TaleaGSM", "ip_address":"10.66.0.10"}'
# Yaviche
curl -v -X PUT http://localhost:8098/buckets/sites/keys/688261 -H "Content-Type: application/json" -d '{"site_name": "Yaviche", "postcode": "68826", "pbxcode": "1", "network_name": "BueXhidza", "ip_address":"10.66.0.34"}'

curl -v -X PUT http://localhost:8098/buckets/sites/keys/66666 -H "Content-Type: application/json" -d '{"site_name": "Boxie", "postcode": "66666", "pbxcode": "1", "network_name": "Boxie", "ip_address":"10.66.0.54"}'

