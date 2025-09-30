## ECサイト新着商品取得（画像認識対応版）

このプロジェクトは、指定されたECサイトから新着商品情報をスクレイピングし、PyTorchで学習させた画像認識モデルを用いて対象商品をフィルタリングし、データベースに保存する自動化ツールです。

## 機能
- **Webスクレイピング**: Seleniumを使い、動的なWebページから商品情報（名前、画像URL、IDなど）を抽出します。
- **画像認識**: PyTorchで学習させたEfficientNetモデルを使用し、収集した商品画像から特定のカテゴリ（例: キャラクターグッズ）に属するものだけを自動で分類します。
- **データベース管理**: 抽出・分類した商品データをMySQL/MariaDBに保存し、重複を排除しながら履歴を管理します。
- **レポート生成**: 最終的に抽出された商品のアフィリエイトリンクを含むHTMLファイルを生成します。（※本テンプレートでは簡略化）

## 必要なもの
- Python 3.9以上
- `requirements.txt` に記載のライブラリ
- 学習済みのPyTorchモデルファイル (`.pth`)
- MySQL または MariaDB データベース

## セットアップ方法

1.  **リポジトリをクローン**
    ```bash
    git clone [https://github.com/your-username/your-repository.git](https://github.com/your-username/your-repository.git)
    cd your-repository
    ```

2.  **仮想環境の作成と有効化**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **必要なライブラリをインストール**
    ```bash
    pip install -r requirements.txt
    ```
    *(注: `requirements.txt`は`pipreqs .`コマンドで生成してください)*

4.  **データベースのセットアップ**
    以下のSQL文を実行し、`data`（履歴保存用）と`update`（実行ごとの更新用）の2つのテーブルを作成します。
    ```sql
    CREATE DATABASE your_db_name;
    USE your_db_name;

    CREATE TABLE `data` (
      `item_id` VARCHAR(255) NOT NULL,
      `name` TEXT,
      `image_url` TEXT,
      `status` VARCHAR(50),
      PRIMARY KEY (`item_id`)
    );

    CREATE TABLE `update` (
      `item_id` VARCHAR(255) NOT NULL,
      `name` TEXT,
      `image_url` TEXT,
      `status` VARCHAR(50),
      PRIMARY KEY (`item_id`)
    );
    ```

5.  **環境変数ファイルの設定**
    `.env.sample`をコピーして`.env`ファイルを作成し、ご自身のデータベース情報を入力します。
    ```bash
    cp .env.sample .env
    ```

6.  **画像認識モデルの配置**
    学習済みのモデルファイル（例: `model.pth`）を、スクリプトと同じ階層に配置してください。

7.  **スクリプトの設定値を編集**
    `your_script_name.py`を開き、冒頭の`# --- 設定ここから ---`の部分にある以下の定数を、あなたの対象サイトに合わせて編集してください。
    - `TARGET_URL_FORMAT`
    - `IMAGE_SAVE_DIR`
    - `CLASSIFIER_MODEL_PATH`
    - `CLASSES`
    - `PRODUCT_NAME_XPATH`, `THUMBNAIL_XPATH`, `TAG_XPATH`

## 実行方法
上記の設定が完了したら、以下のコマンドでプログラムを実行します。
```bash
python your_script_name.py
```