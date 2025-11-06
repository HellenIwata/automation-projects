#!/bin/bash

# Arquivo de saída
OUTPUT="buckets-publicos.txt"
> "$OUTPUT"  # Limpa o conteúdo anterior

# Lista todos os buckets
BUCKETS=$(aws s3api list-buckets --query "Buckets[].Name" --output text)

echo "Buckets públicos encontrados:" >> "$OUTPUT"
echo "-----------------------------" >> "$OUTPUT"



for bucket in $BUCKETS; do
    echo "VERIFICANDO O BUCKET: '$bucket'"

    CONFIG=$(aws s3api get-public-access-block \
        --bucket "$bucket" \
        --query "PublicAccessBlockConfiguration" \
        --output json 2>/dev/null)

    if [ $? -ne 0 ]; then
        echo "$bucket" | tee -a "$OUTPUT"
        continue
    fi

    BLOCK_ACLS=$(echo "$CONFIG" | jq -r '.BlockPublicAcls')
    IGNORE_ACLS=$(echo "$CONFIG" | jq -r '.IgnorePublicAcls')
    BLOCK_POLICY=$(echo "$CONFIG" | jq -r '.BlockPublicPolicy')
    RESTRICT_BUCKET=$(echo "$CONFIG" | jq -r '.RestrictPublicBuckets')

    if [ "$BLOCK_ACLS" = "false" ] || [ "$IGNORE_ACLS" = "false" ] || \
        [ "$BLOCK_POLICY" = "false" ] || [ "$RESTRICT_BUCKET" = "false" ]; then
        echo "$bucket" >> "$OUTPUT"
    fi
done

echo "Resultado salvo em: $OUTPUT"