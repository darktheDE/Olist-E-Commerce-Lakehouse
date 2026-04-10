#!/bin/bash

# Thư mục chứa Jars
JAR_DIR="./jars"
mkdir -p $JAR_DIR

echo "Checking and downloading required jars to $JAR_DIR..."

# Danh sách JARs cần thiết (Version tương ứng với docker-compose.yml)
declare -A JARS=(
    ["postgresql-42.7.4.jar"]="https://jdbc.postgresql.org/download/postgresql-42.7.4.jar"
    ["aws-java-sdk-bundle-1.12.262.jar"]="https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar"
    ["delta-spark_2.12-3.2.0.jar"]="https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.2.0/delta-spark_2.12-3.2.0.jar"
    ["delta-storage-3.2.0.jar"]="https://repo1.maven.org/maven2/io/delta/delta-storage/3.2.0/delta-storage-3.2.0.jar"
    ["hadoop-aws-3.3.4.jar"]="https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar"
    ["antlr4-runtime-4.9.3.jar"]="https://repo1.maven.org/maven2/org/antlr/antlr4-runtime/4.9.3/antlr4-runtime-4.9.3.jar"
    ["wildfly-openssl-1.0.7.Final.jar"]="https://repo1.maven.org/maven2/org/wildfly/openssl/wildfly-openssl/1.0.7.Final/wildfly-openssl-1.0.7.Final.jar"
)

for JAR_NAME in "${!JARS[@]}"; do
    FILE_PATH="$JAR_DIR/$JAR_NAME"
    if [ ! -f "$FILE_PATH" ]; then
        echo "Downloading $JAR_NAME..."
        curl -L "${JARS[$JAR_NAME]}" -o "$FILE_PATH"
    else
        echo "$JAR_NAME already exists, skipping."
    fi
done

echo "Done! All jars are ready in $JAR_DIR."
