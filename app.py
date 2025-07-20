from flask import Flask, request, jsonify import asyncio from Crypto.Cipher import AES from Crypto.Util.Padding import pad from google.protobuf.json_format import MessageToJson import binascii import aiohttp import requests import json import like_pb2 import like_count_pb2 import uid_generator_pb2

Initialize Flask app

app = Flask(name)

Load tokens based on region

def load_tokens(server_name): server_name = server_name.upper() if server_name == "IND": filename = "token_ind.json" elif server_name in {"BR", "US", "SAC", "NA"}: filename = "token_br.json" else: filename = "token_bd.json" with open(filename, "r") as f: return json.load(f)

AES encryption helper

def encrypt_message(plaintext_bytes): key = b'Yg&tc%DEuh6%Zc^8' iv = b'6oyZDr22E3ychjM%' cipher = AES.new(key, AES.MODE_CBC, iv) padded = pad(plaintext_bytes, AES.block_size) encrypted = cipher.encrypt(padded) return binascii.hexlify(encrypted).decode('utf-8')

Protobuf builders

def create_like_proto(uid, region): msg = like_pb2.like() msg.uid = int(uid) msg.region = region return msg.SerializeToString()

def create_uid_proto(uid): msg = uid_generator_pb2.uid_generator() # Generated fields: saturn_ and garena msg.saturn_ = int(uid) msg.garena = 1 return msg.SerializeToString()

Async HTTP for sending likes

async def send_request(encrypted_hex, token, url): data = bytes.fromhex(encrypted_hex) headers = { 'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)", 'Authorization': f"Bearer {token}", 'Content-Type': "application/x-www-form-urlencoded", } async with aiohttp.ClientSession() as session: async with session.post(url, data=data, headers=headers) as resp: return resp.status

async def send_multiple_likes(uid, region_url, token): proto = create_like_proto(uid, region_url) enc_hex = encrypt_message(proto) tasks = [send_request(enc_hex, token, region_url) for _ in range(100)] await asyncio.gather(*tasks)

Sync HTTP request wrapper

def make_request(encrypted_hex, token, url): headers = { 'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)", 'Authorization': f"Bearer {token}", 'Content-Type': "application/x-www-form-urlencoded", } resp = requests.post(url, data=bytes.fromhex(encrypted_hex), headers=headers, verify=False) resp.raise_for_status() return resp.content

Decode Protobuf Info message

def decode_info(raw_bytes): info = like_count_pb2.Info() info.ParseFromString(raw_bytes) return info

Flask route

@app.route('/like', methods=['GET']) def handle_requests(): try: uid = request.args.get('uid') server_name = request.args.get('server_name', '').upper() if not uid or not server_name: return jsonify({'error': 'uid and server_name are required'}), 400

# Determine endpoints based on region
    if server_name == 'IND':
        show_url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
        like_url = "https://client.ind.freefiremobile.com/LikeProfile"
    elif server_name in {'BR', 'US', 'SAC', 'NA'}:
        show_url = "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
        like_url = "https://client.us.freefiremobile.com/LikeProfile"
    else:
        show_url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"
        like_url = "https://clientbp.ggblueshark.com/LikeProfile"

    # Load token list
    tokens = load_tokens(server_name)
    token = tokens[0]['token']

    # Prepare encrypted UID for "show"
    uid_proto = create_uid_proto(uid)
    enc_uid_hex = encrypt_message(uid_proto)

    # 1) Get before info
    raw_before = make_request(enc_uid_hex, token, show_url)
    info_before = decode_info(raw_before)
    before_likes = info_before.AccountInfo.Likes
    player_id = info_before.AccountInfo.UID
    nickname = info_before.AccountInfo.PlayerNickname

    # 2) Send likes asynchronously
    asyncio.run(send_multiple_likes(uid, like_url, token))

    # 3) Get after info
    raw_after = make_request(enc_uid_hex, token, show_url)
    info_after = decode_info(raw_after)
    after_likes = info_after.AccountInfo.Likes

    # Calculate results
    likes_delta = after_likes - before_likes
    status = 1 if likes_delta > 0 else 2

    result = {
        'UID': player_id,
        'Name': nickname,
        'BeforeLikes': before_likes,
        'AfterLikes': after_likes,
        'LikesGivenByAPI': likes_delta,
        'Status': status
    }
    return jsonify(result), 200

except requests.HTTPError as http_err:
    return jsonify({'error': f'HTTP error: {http_err}'}), 500
except Exception as e:
    return jsonify({'error': str(e)}), 500

WSGI entrypoint

if name == 'main': app.run(debug=True, host='0.0.0.0', port=3000)

