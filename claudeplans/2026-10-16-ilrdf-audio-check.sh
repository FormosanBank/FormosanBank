#!/usr/bin/env bash
# Downloads main's recording (Hugging Face) and the 2026 ILRDF recording for 9 ILRDF sentence pairs,
# into claudeplans/ilrdf-audio-check/ (mp3s are gitignored). Run from the FormosanBank checkout root on the Mac.
# If the HF dataset needs a login: export HF_TOKEN=... first.
set -u
cd "$(dirname "$0")/.." || exit 1
D=claudeplans/ilrdf-audio-check; mkdir -p "$D"
AUTH=(); [ -n "${HF_TOKEN:-}" ] && AUTH=(-H "Authorization: Bearer $HF_TOKEN")
get() {  # id n main_url new_url
  [ -s "$D/$1.main.mp3" ] || curl -sfL ${AUTH[@]+"${AUTH[@]}"} -o "$D/$1.main.mp3" "$3" || echo "FAILED main $1"
  curl -sfL -o "$D/$1.2026_$2.mp3" "$4" || echo "FAILED 2026 $1"
}
get Kavalan_363 1 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Kavalan/Kavalan/Kavalan_363.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/f545cbb2-6781-43df-8098-32d0250dc2ab/download'
get Kavalan_6619 1 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Kavalan/Kavalan/Kavalan_6619.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/64b710f5-6973-4dd9-973a-43a0d6fc7db8/download'
get Paiwan_5229 1 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Paiwan/Paiwan/Paiwan_5229.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/fcbef0fb-eea6-43ad-87c0-4316d36d4c62/download'
get Saaroa_1398 1 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Saaroa/Saaroa/Saaroa_1398.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/21901b72-c20b-4f84-8ea3-55df85045ae5/download'
get Saisiyat_2423 1 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Saisiyat/Saisiyat/Saisiyat_2423.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/b57c0e6c-40b7-4b02-ae3b-ddeba42b698c/download'
get Seediq_268 1 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Seediq/Seediq/Seediq_268.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/bde7fab5-31ea-4517-9c81-c7bea9db6ac8/download'
get Tsou_275 1 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Tsou/Tsou/Tsou_275.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/90d4822f-df03-4ef9-8b66-8a79af044358/download'
get Kanakanavu_2310 1 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Kanakanavu/Kanakanavu/Kanakanavu_2310.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/16185102-bbb9-4863-82d1-93b3d80651b9/download'
get Kanakanavu_5468 1 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Kanakanavu/Kanakanavu/Kanakanavu_5468.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/428afecc-c54f-4972-a4dd-9e6ed6b9bd6a/download'
get Yami_4596 1-Langdao 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Yami/Yami/Yami_4596.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/42923b3b-b8d6-48ee-9d27-f580b456b2e5/download'
get Yami_4596 2-Yeyin 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Yami/Yami/Yami_4596.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/16b5464d-19e3-417b-a21f-991e0616dc81/download'
get Yami_4596 3-Yuren 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Yami/Yami/Yami_4596.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/36ec7103-7b7a-4880-a0e1-f99c2d7e5bae/download'
get Yami_10 1-Langdao 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Yami/Yami/Yami_10.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/ed161356-c8d5-430d-b41a-40900de13cc5/download'
get Yami_10 2-Yeyin 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Yami/Yami/Yami_10.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/8e39a919-eca2-4639-9461-d26e5a498877/download'
get Yami_10 3-Yuren 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Yami/Yami/Yami_10.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/255fe58b-a0cf-44f5-b9a6-5b685da590eb/download'
get Yami_11 1-Langdao 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Yami/Yami/Yami_11.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/7034dabd-6a36-419a-8d5a-2f02d794221c/download'
get Yami_11 2-Yeyin 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Yami/Yami/Yami_11.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/fbead502-2adc-45c7-b7a9-e437c13dbc69/download'
get Yami_11 3-Yuren 'https://huggingface.co/datasets/FormosanBank/ILRDF_Dicts/resolve/main/Yami/Yami/Yami_11.mp3' 'https://sys-dictionary.ilrdf.org.tw/Data/api/Storage/7b32d4d8-9f65-4b26-8395-a161061a949c/download'
ls -l "$D"
