from flask import Flask, request, jsonify import asyncio from Crypto.Cipher import AES from Crypto.Util.Padding import pad from google.protobuf.json_format import MessageToJson import binascii import aiohttp from google.protobuf.json_format import MessageToDict import requests import json import like_pb2 import like_count_pb2 import uid_generator_pb2

app = Flask(name)

def load_tokens(server_name): if server_name == "IND": with open("token_ind.json", "r") as f: return json.load(f) elif server_name in {"BR", "US", "SAC", "NA"}: with open("token_br.json", "r") as f: return json.load(f) else: with open("token_bd.json", "r") as f: return json.load(f)

def encrypt_message(plaintext): key = b'Yg&tc%DEuh6%Zc^8' iv = b'6oyZDr22E3ychjM%' cipher = AES.new(key, AES.MODE_CBC, iv) padded_message = pad(plaintext, AES.block_size) encrypted_message = cipher.encrypt(padded_message) return binascii.hexlify(encrypted_message).decode('utf-8')

def create_protobuf_message(user_id, region): message = like_pb2.like() message.uid = int(user_id) message.region = region return message.SerializeToString()

async def send_request(encrypted_uid, token, url): edata = bytes.fromhex(encrypted_uid) headers = { 'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)", 'Connection': "Keep-Alive", 'Accept-Encoding': "gzip", 'Authorization': f"Bearer {token}", 'Content-Type': "application/x-www-form-urlencoded", 'Expect': "100-continue", 'X-Unity-Version': "2018.4.11f1", 'X-GA': "v1 1", 'ReleaseVersion': "OB48" } async with aiohttp.ClientSession() as session: async with session.post(url, data=edata, headers=headers) as response: if response.status != 200: print(f"Request failed with status code: {response.status}") return response.status

async def send_multiple_requests(uid, server_name, url): region = server_name protobuf_message = create_protobuf_message(uid, region) encrypted_uid = encrypt_message(protobuf_message) tokens = load_tokens(server_name) tasks = [send_request(encrypted_uid, tokens[i % len(tokens)]['token'], url) for i in range(100)] await asyncio.gather(*tasks)

def create_uid_protobuf(uid): message = uid_generator_pb2.uid_generator() # field names as generated: use correct attributes # Note: the generated .proto fields are saturn_ and garena message.saturn_ = int(uid) message.garena = 1 return message.SerializeToString()

def enc(uid): protobuf_data = create_uid_protobuf(uid) return encrypt_message(protobuf_data)

def make_request(encrypted_hex, server_name, token, endpoint): if endpoint == 'show': if server_name == "IND": url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow" elif server_name in {"BR", "US", "SAC", "NA"}: url = "https://client.us.freefiremobile.com/GetPlayerPersonalShow" else: url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow" else:  # like if server_name == "IND": url = "https://client.ind.freefiremobile.com/LikeProfile" elif server_name in {"BR", "US", "SAC", "NA"}: url = "https://client.us.freefiremobile.com/LikeProfile" else: url = "https://clientbp.ggblueshark.com/LikeProfile"

data = bytes.fromhex(encrypted_hex)
headers = {
    'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
    'Connection': "Keep-Alive",
    'Accept-Encoding': "gzip",
    'Authorization': f"Bearer {token}",
    'Content-Type': "application/x-www-form-urlencoded",
    'Expect': "100-continue",
    'X-Unity-Version': "2018.4.11f1",
    'X-GA': "v1 1",
    'ReleaseVersion': "OB48"
}
resp = requests.post(url, data=data, headers=headers, verify=False)
return resp.content

def decode_info(content_bytes): try: info = like_count_pb2.Info() info.ParseFromString(content_bytes) return info except Exception as e: raise ValueError(f"Protobuf decode error: {e}")

@app.route('/like', methods=['GET']) def handle_requests(): try: uid = request.args.get("uid") server_name = request.args.get("server_name", "").upper() if not uid or not server_name: return jsonify({"error": "UID and server_name are required"}), 400

tokens = load_tokens(server_name)
    token = tokens[0]['token']
    encrypted_hex = enc(uid)

    # 1) Get before show info
    show_bytes = make_request(encrypted_hex, server_name, token, 'show')
    info_before = decode_info(show_bytes)
    before_like = info_before.AccountInfo.Likes
    player_id = info_before.AccountInfo.UID
    nickname = info_before.AccountInfo.PlayerNickname

    # 2) Send likes
    asyncio.run(send_multiple_requests(uid, server_name, ''))

    # 3) Get after show info
    show_bytes_after = make_request(encrypted_hex, server_name, token, 'show')
    info_after = decode_info(show_bytes_after)
    after_like = info_after.AccountInfo.Likes

    # Compute result
    likes_given = after_like - before_like
    status = 1 if likes_given > 0 else 2
    result = {
        "UID": player_id,
        "Name": nickname,
        "BeforeLikes": before_like,
        "AfterLikes": after_like,
        "LikesGivenByAPI": likes_given,
        "Status": status
    }
    return jsonify(result), 200
except Exception as e:
    return jsonify({"error": str(e)}), 500

if name == 'main': app.run(debug=True, host='0.0.0.0')

