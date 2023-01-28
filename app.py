# coding: utf -8
import PySimpleGUI as sg  # ライブラリの読み込み
import re

# テーマの設定
sg.theme("Dark Blue 3 ")

# ドメイン設定
L1 = [
    # エンディアン変換
    [sg.Text("・エンディアン変換 ", size=(20, 1)),
     sg.OptionMenu(["変換なし", "変換あり"],
                   background_color="#ffffff",
                   default_value="変換なし",
                   size=(10, 1),
                   key="-ENDIAN-")],
    # 開始アドレス
    [sg.Text("・開始アドレス ", size=(20, 1)),
     sg.InputText(default_text="00000000",
                  text_color="#000000",
                  background_color="#ffffff",
                  key="-ADDRESS-",
                  size=(15, 1))],
    # データ
    [sg.Text("・書き込みデータ", size=(40, 1))],
    [sg.Multiline(text_color="#000000",
                  background_color="#ffffff",
                  size=(100, 10),
                  key="-INPUT_TXT-")],
    # S3レコード
    [sg.Text("・S3レコード", size=(40, 1))],
    [sg.Multiline(text_color="#000000",
                  background_color="#ffffff",
                  size=(100, 10),
                  key="-S3_TXT-")],
    [sg.Button("実行", border_width=4, size=(15, 1), key="start")]]
# ウィンドウ作成
window = sg.Window("S-record_TOOL ", L1)


def main():
    # イベントループ
    while True:
        # イベントの読み取り（イベント待ち）
        event, values = window.read()
        if event == "start":
            # 不要要素の削除
            input_txt = re.sub('[^0123456789abcdefABCDEF]',
                               '', values["-INPUT_TXT-"])
            # サイズチェック
            if 8 == len(values["-ADDRESS-"]):
                if 0 == (len(input_txt) % 8):
                    output_txt = make_record_fnc(values["-ENDIAN-"], values["-ADDRESS-"], input_txt)
                    window["-S3_TXT-"].Update(output_txt)
                else:
                    sg.popup_error('書き込みデータは4byte単位で入力してください',title = "入力値不正")
                    pass
            else:
                sg.popup_error('アドレスは4byte単位で入力してください',title = "入力値不正")
                pass
        # 終了条件（ None: クローズボタン）
        elif event is None:
            break
    # 終了処理
    window.close()


def make_record_fnc(endian,address,data):
    BYTE_DATA = bytes.fromhex(data)
    BYTE_LEN = len(BYTE_DATA)
    S3_MAX_WRITE_DATA = 16
    S3_MAX_LOW = -(-BYTE_LEN // S3_MAX_WRITE_DATA) # 切り上げ
    write_offset = 0
    return_data = ""
    # S3レコード作成
    for write_low in range(S3_MAX_LOW):
        write_offset = write_low*S3_MAX_WRITE_DATA
        # 16byte単位のS3レコード作成
        if 16 <= BYTE_LEN - write_offset:
            s3_addr = int("0x"+address,16) + write_offset
            # エンディアン変換
            if "変換なし" == endian:
                s3_data = BYTE_DATA[write_offset:write_offset+S3_MAX_WRITE_DATA]
            else:
                s3_data = make_chenge_endian(BYTE_DATA[write_offset:write_offset+S3_MAX_WRITE_DATA])
            # チェックサム算出
            s3_chk_sum_data = b"\x15" + bytes.fromhex(format(s3_addr, '08x')) + s3_data
            s3_chk_sum = hex(255-sum(s3_chk_sum_data)%256)
            s3_record = "S3" + s3_chk_sum_data.hex() + s3_chk_sum[2:].zfill(2)
            # オフセット更新
            write_offset += S3_MAX_WRITE_DATA
            return_data += s3_record + "\n"
        # 16byte未満のS3レコード作成
        elif 0 < BYTE_LEN - write_offset:
            s3_addr = int("0x"+address,16) + write_offset
            s3_len = 5+len(BYTE_DATA[write_offset:])
            # エンディアン変換
            if "変換なし" == endian:
                s3_data = BYTE_DATA[write_offset:]
            else:
                s3_data = make_chenge_endian(BYTE_DATA[write_offset:])
            # チェックサム算出
            s3_chk_sum_data = s3_len.to_bytes(1,"big") + bytes.fromhex(format(s3_addr, '08x')) + s3_data
            s3_chk_sum = hex(255-sum(s3_chk_sum_data)%256)
            s3_record = "S3" + s3_chk_sum_data.hex() + s3_chk_sum[2:].zfill(2)
            return_data += s3_record + "\n"
            pass
        else:
            break
    return return_data

def make_chenge_endian(data):
    return_data = bytearray(data)
    for i in range(len(data)):
        return_data[i] = data[(i//4)*4 + (3-i%4)]
    return return_data

if __name__ == '__main__':
    main()
