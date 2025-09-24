# github掲載用物体検出利用新製品情報取得コード

import numpy as np
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import re
import hashlib
import requests
import mysql.connector
import os
import glob
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ChromeOptionsを設定
options = Options()
# ヘッドレスモードを有効にする
options.add_argument('--headless=new') 

# 物体検出用
from ultralytics import YOLO
from PIL import Image
import matplotlib.pyplot as plt
import io

# 環境設定
from dotenv import load_dotenv
import os
load_dotenv()

# --- パラメータ設定部分 ---
DEBUG_MODE = False # Trueにすると画像が表示される、普段はFalse


# 商品名短縮関数
def shorten_product_name(text):
  """商品名を一行で表示できる程度に短縮する

  Args:
    text: 商品名

  Returns:
    短縮された商品名
  """
  text = re.sub(r"送料無料◆", "", text) #　適宜商品名の条件愛合わせて追加

  return text

def scrape_page_data(page_number):
    """指定されたページ番号の商品情報をスクレイピングし、リストとして返す"""
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        url = f'ECサイトの商品情報一覧ページ{page_number}' # page_numberにページ数を割り当ててクロールする
        driver.get(url)
        
        # 要素が表示されるまで最大15秒待機
        WebDriverWait(driver,15).until(
            EC.presence_of_element_located((By.CLASS_NAME,'クラス名'))
        )
    
        # 1. サムネイル要素や名前要素などをまとめて取得
        thumbnails = driver.find_elements(By.CSS_SELECTOR,'適宜セレクタを追加')
        name_elements = driver.find_elements(By.CSS_SELECTOR, '適宜セレクタを追加')
        
        # 2. 商品名リストを作成
        name_list = [elem.text for elem in name_elements]
    
        # 3　IDと画像URLのリストを
        ID_list = []
        Image_urls = []
    
        # 商品IDと画像URLの取得（構造変更対応: CSSセレクタでリンクと画像を取得）
        for i, thumbnail in enumerate(thumbnails):
            try:
                image_url = thumbnail.get_attribute('src')
                Image_urls.append(image_url)
                
                # 商品リンクからID抽出（hrefからitemcodeを抽出）
                link_elem = thumbnail.find_element(By.XPATH, './ancestor::a')  # 画像の親aタグ
                href = link_elem.get_attribute('href')
                item_id = href.split('/')[-1].split('.')[0]  # URLからID部分を抽出 (例: yp158288.html → yp158288)
                ID_list.append(item_id)
            except Exception as e:
                print(f"ページ {page_number} で商品IDまたは画像URLの取得に失敗しました: {e}")
                ID_list.append("N/A")
                Image_urls.append("N/A")

        # 商品名を短縮
        name_list = [shorten_product_name(name) for name in name_list]
        # リストを連結する
        product_list = [list(item) for item in zip(name_list, Image_urls, ID_list)]
         
        return product_list
        
    
    except Exception as e:
        print(f"ページ {page_number} の処理中にエラー: {e}")
        return []

    finally:
        if driver:
            driver.quit()


def process_and_filter_product(product_data, model):
    """
    1つの商品データを処理し、物体検出でフィルタリングする。
    採用ならば全情報タプルを、不採用ならばNoneを返す。
    """
    # １.生データを取り出す
    name, image_url, item_id = product_data

    # w.　ハッシュ値を計算する
    if image_url and 'http' in image_url:
        try:
            image_data  = requests.get(image_url, timeout=10).content
            image_hash = hashlib.sha256(image_data).hexdigest()
        except Exception:
            image_data = None
            image_hash = 'download_failed'

    else:
        image_data = None
        image_hash = 'download_failded'

    product_key = hashlib.sha256((name + item_id).encode()).hexdigest()

    
    # 3. 物体検出を実行して判断
    is_target_detected = False
    if image_data:
        try:
            # メモリ上から画像を直接読み込む
            image = Image.open(io.BytesIO(image_data))
            results = model.predict(image, verbose=False)
            if len(results[0].boxes) > 0:
                is_target_detected = True
    
        except Exception as e:
            print(f"物体検出エラー：{item_id}, {e}")
    # 結果を返す 
    if  is_target_detected:
        print(f"採用:{name}")
        return (product_key, name, item_id, image_url, image_hash)
    
    else:
        print(f" スルー: {name}")
        return None

def update_database(accepted_products, c):
    """採用された商品リストを元に、データベースを更新する"""
    for new_toy in accepted_products:
        product_key, name, item_id, image_url, image_hash = new_toy
        
        sql = "SELECT * FROM `new` WHERE `Product_key` = %s"
        c.execute(sql, (product_key,))
        fig = c.fetchone()
        
        if not fig: # 新しい商品の場合
            # アーカイブテーブルに追加
            query_new = ("INSERT INTO new"
                         "(Product_key, Product_name, Item_id, Image_url, Image_hash)"
                         "VALUES (%s, %s, %s, %s, %s)")
            c.execute(query_new, (product_key, name, item_id, image_url, image_hash))
            
            # 更新テーブルにも追加
            query_update = ("INSERT INTO update"
                            "(Product_key, Product_name, Item_id, Image_url, Image_hash)"
                            "VALUES (%s, %s, %s, %s, %s)")
            c.execute(query_update, (product_key, name, item_id, image_url, image_hash))

        else: # 既に存在する商品の場合
            # 画像ハッシュを比較して、画像が更新されているかチェック
            sql_check_hash = "SELECT * FROM `new` WHERE `Product_key` = %s AND `Image_hash` = %s"
            c.execute(sql_check_hash, (product_key, image_hash))
            fig_with_same_hash = c.fetchone()

            if not fig_with_same_hash: # 画像が更新されている場合
                # 古い情報を更新（UPDATE文の方が効率的）
                query_update_archive = ("UPDATE new SET "
                                        "Product_name=%s, Item_id=%s, Image_url=%s, Image_hash=%s "
                                        "WHERE Product_key=%s")
                c.execute(query_update_archive, (name, item_id, image_url, image_hash, product_key))

                # 更新テーブルに（存在しなければ）追加
                query_insert_update = ("INSERT IGNORE INTO update"
                                       "(Product_key, Product_name, Item_id, Image_url, Image_hash)"
                                       "VALUES (%s, %s, %s, %s, %s)")
                c.execute(query_insert_update, (product_key, name, item_id, image_url, image_hash))


def main():
    # ... 準備（DB接続、モデル読み込み）
    try:
        print("--- チェックポイント1: main関数開始 ---")

        
        # データベース接続
        # 別に.envファイルを作成:
        # .gitignoreファイルに.envを追加して、GitHubにアップロードされないようにする
        conn = mysql.connector.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        charset='utf8mb4'
        )
        c = conn.cursor()

        # 物体検出用データ読み込み
        # ステップ1：学習させたカスタムモデルのパスを指定
        model_path = 'best.pt' # モデルは事前に準備必要 Roboflowなどで準備
        # ステップ2：モデルを読み込む
        model = YOLO(model_path)
        
        # updateテーブルを最初に空にする
        c.execute("TRUNCATE TABLE `update`")
        print("--- チェックポイント2: updateテーブルのクリア完了 ---")
    
        
        # --- メイン処理 ---
        accepted_products = []
        for page_num in range(0, 5):
            raw_products = scrape_page_data(page_num)
            
            for product in raw_products:
                filtered_result = process_and_filter_product(product, model)
                if filtered_result: # 結果がNoneでなければ（採用されたら）
                    accepted_products.append(filtered_result)
            print(f"--- チェックポイント3: AIフィルタリング完了、採用数: {len(accepted_products)} ---")
            
                 
        # --- 3. データベース操作 ---
        update_database(accepted_products, c)
        print("--- チェックポイント4: データベース更新処理完了 ---")
        
        # --- 4. DB変更を【最後に一度だけ】確定 ---
        conn.commit()
        print("--- チェックポイント5: コミット完了 ---")
                         
        # Mysqlで取得した新規データを出力する
        rows = []
        c.execute('SELECT * FROM `digiY_f_p_update_detect2`')
        for row in c.fetchall():
            rows.append(row)

        print("\n--- HTML生成用のデータチェック ---")
        print(f"取得したレコード数: {len(rows)}")
        if len(rows) > 0:
            print("最初のレコード:", rows[0])
        
        # 画像リンクとアフィリエイトリンク作成
        degiy_link = '<a href="個々のアフィリエイトリンクURLP1P2</a>'
        
        yahoo_image_html_list = [] # 画像HTMLを格納するリスト
        yahoo_text_html_list = [] # テキストHTMLを格納するリスト
        
        # HTML_A、HTML_Bのリストを同時にアフィリエイトリンクに挿入する
        for key, name, item_id, image_url, image_hash in rows:
            # 商品名を短縮
            name = shorten_product_name(name)
            
        
            # 画像部分のHTML
            image_html = f"""
            <a class="photoA" href="個々のアフィリエイトリンク{item_id}.html" rel="nofollow">
                <img src="{image_url}" alt="{name.replace('_', '')}" loading="lazy" decoding="async">
            </a>
            """
            yahoo_image_html_list.append(image_html)
        
            # テキスト部分のHTML
            text_html = f"""
            <br><a href="個々のアフィリエイトリンク{item_id}.html" rel="nofollow">{name}</a>
            """
            yahoo_text_html_list.append(text_html)
        
        # HTMLを結合
        image_html = ''.join(yahoo_image_html_list)
        text_html = ''.join(yahoo_text_html_list)
        
        # 全体のHTML
        html_Y = f'<br>(ECサイト名)<br>{image_html}<br>{text_html}<br>'
        with open('新製品アフィリエイトリンク.txt', 'w') as f:
            f.write(html_Y)
        print("--- チェックポイント6: HTML生成完了 ---")
        
        # MySQLデータベースとの接続を閉じる
        conn.commit()
        conn.close()

    except Exception as e:
        print(f"メイン処理でエラーが発生しました: {e}")

    finally:
        # ... 後片付け ...
        print("終了")

            
if __name__ == "__main__":
    main()