#!/bin/bash

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Run MongoDB container
docker run -d -p 27017:27017 --name mongodb-container -e MONGODB_INITDB_ROOT_USERNAME=$MONGO_USER -e MONGODB_INITDB_ROOT_PASSWORD=$MONGO_PASS mongodb/mongodb-community-server:latest

# Wait for MongoDB server to start
echo "Waiting for MongoDB server to start..."
sleep 10  # Adjust the sleep time if necessary

# Secure MongoDB
mongosh --host localhost --port 27017 -u $MONGO_USER -p $MONGO_PASS --authenticationDatabase admin <<EOF
use admin
db.createUser({
  user: "secureUser",
  pwd: "securePassword",
  roles: [{ role: "readWrite", db: "FGOCanItFarmDatabase" }]
})
EOF

echo "MongoDB setup and secured successfully!"
