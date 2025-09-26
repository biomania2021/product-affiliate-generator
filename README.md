## プログラムの動作
このスクリプトは、実行するたびに更新用テーブルをクリアし、その時点で取得した新製品情報だけを処理・出力します。そのため、何度実行しても同じページからは同じ結果が得られ、動作を簡単に確認できます。

## 実際の運用について
実際のブログ自動更新では、このスクリプトの`TRUNCATE`文を削除し、一日の更新を蓄積します。そして、深夜0時に別のスケジュールされたタスク（例: cronジョブ）で更新用テーブルをリセットする、という運用を想定しています。

## 機能
webスクレイピング、YOLOによる物体検出、データベースへの自動登録、HTML生成

## 必要なもの
Python3.12.2
requirements.txt
## セットアップ方法
１．リポジトリのクローン
まずこのリポジトリをローカルマシンにクローンします。

git clone https://github.com/your-username/your-repository.git
cd your-repository

２．Python仮想環境の作成と有効化
プロジェクト専用の仮想環境を作成し、有効化します。これにより、PCの他のPython環境を汚さずにライブラリ管理できます。

# 仮想環境を作成 (venvという名前のフォルダが作られます)
python3 -m venv venv

# 仮想環境を有効化 (Linux/macOS)
source venv/bin/activate

# (Windowsの場合)
# venv\Scripts\activate

３．必要なライブラリをインストール
ewquirements.txtファイルを使って、プロジェクトに必要なライブラリをすべてインストールします。

pip install -r requirements.txt

４．データベースのセットアップ
このプログラムはMySQL(MariaDB)を使用します。以下のSQL文を実行して、必要なデータベースとテーブルを２つ作成してください。

SQL
-- データベースを作成 (既にあれば不要)
CREATE DATABASE HERO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

-- データベースを選択
USE HERO;

-- 1. 全ての検知済み商品を保管するテーブル
CREATE TABLE `new` (
  `Product_key` VARCHAR(64) NOT NULL,
  `Product_name` TEXT,
  `Item_id` VARCHAR(255),
  `Image_url` TEXT,
  `Image_hash` VARCHAR(64),
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`Product_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. 実行ごとに更新される商品情報を一時的に保管するテーブル
CREATE TABLE `update` (
  `Product_key` VARCHAR(64) NOT NULL,
  `Product_name` TEXT,
  `Item_id` VARCHAR(255),
  `Image_url` TEXT,
  `Image_hash` VARCHAR(64),
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`Product_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

５．環境変数ファイルの設定
データベースの接続情報など、機密情報を設定するための.envファイルを作成します。

まず、.env.exampleファイルをコピーして.envファイルを作成します。

cp .env.example .env

次に、作成した.envファイルを開き、ご自身の環境に合わせて値を設定してください。

# MySQL(MariaDB)
DB_USER="あなたのDBユーザー名"
DB_PASSWORD="あなたのDBパスワード"
DB_HOST="127.0.0.1"
DB_DATABASE="HERO"
DB_CHARSET="utf8mb4"

6. 物体検出モデルの配置
学習済みのYOLOモデル（best.pt）を、このプロジェクトのルートディレクトリ（main.pyなどと同じ場所）に配置してください


実行方法
上記の設定が完了したら、以下のコマンドでプログラムを実行します。

python your_script_name.py

実行すると、program.logにログが記録され、新製品アフィリエイトリンク.txtに結果が出力されます。