from flask import Flask, request, jsonify import asyncio from Crypto.Cipher import AES from Crypto.Util.Padding import pad from google.protobuf.json_format import MessageToJson import binascii import aiohttp import requests import json import like_pb2 import like_count_pb2 import uid_generator_pb2

app = Flask(name)

Load only one token file; region selection handled by reading same tokens

def load_tokens(): with open("token_ind.json", "r") as f: return json.load(f)

AES encryption helper

def encrypt_message(plaintext): key = b'Yg&tc%DEuh6%Zc^8' iv = b'6oyZDr22E3ychjM%' cipher = AES.new(key, AES.MODE_CBC, iv) padded = pad(plaintext, AES.block_size) return binascii.hexlify(cipher.encrypt(padded)).decode()

Create like protobuf

def create_like_proto(uid, region): msg = like_pb2.like() msg.uid = int(uid) msg.region = region return msg.SerializeToString()

Create UID generator protobuf

def create_uid_proto(uid): msg = uid_generator_pb2.uid_generator() msg.saturn_ = int(uid) msg.garena = 1 return msg.SerializeToString()

Asynchronous send

async def send_request(encrypted_hex, token, url): data = bytes.fromhex(encrypted_hex) headers = { 'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)", 'Authorization': f"Bearer {token}", 'Content-Type': "application/x-www-form-urlencoded", } async with aiohttp.ClientSession() as session: async with session.post(url, data=data, headers=headers) as resp: return resp.status

async def send_multiple_like(uid, region_url, token): proto = create_like_proto(uid, region_url) enc = encrypt_message(proto) tasks = [send_request(enc, token, region_url) for _ in range(100)] await asyncio.gather(*tasks)

Make sync request; endpoint type: 'show' or 'like'

def make_request(encrypted_hex, token, endpoint_url): resp = requests.post(endpoint_url, data=bytes.fromhex(encrypted_hex), headers={ 'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)", 'Authorization': f"Bearer {token}", 'Content-Type': "application/x-www-form-urlencoded", }, verify=False) return resp.content

Decode protobuf to Info

def decode_info(content_bytes): info = like_count_pb2.Info() info.ParseFromString(content_bytes) return info

@app.route('/like', methods=['GET']) def handle_requests(): try: uid = request.args.get('uid') region = request.args.get('server_name', '').upper() if not uid or not region: return jsonify({'error': 'uid and server_name required'}), 400

# Determine URLs
    if region == 'IND':
        base_show = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
        base_like = "https://client.ind.freefiremobile.com/LikeProfile"
    else:
        base_show = "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
        base_like = "https://client.us.freefiremobile.com/LikeProfile"

    tokens = load_tokens()
    token = tokens[0]['token']

    # Generate uid proto
    uid_proto = create_uid_proto(uid)
    enc_uid = encrypt_message(uid_proto)

    # 1) Before show
    before_bytes = make_request(enc_uid, token, base_show)
    info_before = decode_info(before_bytes)
    before_likes = info_before.AccountInfo.Likes

    # 2) Send likes
    asyncio.run(send_multiple_like(uid, base_like, token))

    # 3) After show
    after_bytes = make_request(enc_uid, token, base_show)
    info_after = decode_info(after_bytes)
    after_likes = info_after.AccountInfo.Likes

    # Prepare result
    delta = after_likes - before_likes
    result = {
        'UID': info_after.AccountInfo.UID,
        'Name': info_after.AccountInfo.PlayerNickname,
        'BeforeLikes': before_likes,
        'AfterLikes': after_likes,
        'LikesGivenByAPI': delta,
        'Status': 1 if delta > 0 else 2
    }
    return jsonify(result), 200
except Exception as e:
    return jsonify({'error': str(e)}), 500

if name == 'main': app.run(debug=True, host='0.0.0.0')

