###############################################
# script_crypto_automation.py
###############################################
import os
import sys
import requests
import json
import datetime
import pymysql
import feedparser
import datetime
from datetime import timezone
from dotenv import load_dotenv

# 1. Chargement des variables d'environnement
load_dotenv()  # Charge les variables définies dans .env

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "crypto_video")

COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY", "")
LUNARCRUSH_API_KEY = os.getenv("LUNARCRUSH_API_KEY", "")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
BITQUERY_API_KEY = os.getenv("BITQUERY_API_KEY", "")

CRYPTO_NEWS_RSS_URL = os.getenv("CRYPTO_NEWS_RSS_URL", "https://cointelegraph.com/rss")

# Endpoints si vous en avez besoin
COINMARKETCAP_BASE_URL = "https://pro-api.coinmarketcap.com/v1"
LUNARCRUSH_BASE_URL = "https://api.lunarcrush.com/v2"
ETHERSCAN_BASE_URL = "https://api.etherscan.io/api"

# --------------------------------------------------------------------
# 2. Connexion à la base de données
# --------------------------------------------------------------------
def get_db_connection():
    """
    Établit la connexion à la base de données MySQL.
    """
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except pymysql.MySQLError as e:
        print(f"Erreur lors de la connexion à la base de données : {e}")
        sys.exit(1)

# --------------------------------------------------------------------
# 3. FONCTIONS DE COLLECTE DES DONNÉES
# --------------------------------------------------------------------

def fetch_rss_data(rss_url):
    """
    Récupère des articles depuis un flux RSS (titre, lien, date).
    """
    feed = feedparser.parse(rss_url)
    articles = []
    for entry in feed.entries[:5]:  # on ne prend que les 5 derniers articles
        published_datetime = None
        if hasattr(entry, 'published_parsed'):
            try:
                published_datetime = datetime.datetime(*entry.published_parsed[:6])
            except:
                published_datetime = None

        articles.append({
            "title": entry.title,
            "link": entry.link,
            "published": published_datetime
        })
    return articles

def analyze_market_sentiment():
    """
    Exemple: Utilise LunarCrush (ou autre API) pour estimer le sentiment du marché.
    Retourne un dict contenant un % positif/neutre/négatif.
    """
    url = f"{LUNARCRUSH_BASE_URL}?data=market"
    params = {
        "key": LUNARCRUSH_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Traitement fictif de la réponse
        sentiment_example = {
            "positive": 60,
            "neutral": 30,
            "negative": 10
        }
        return sentiment_example

    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'appel API LunarCrush : {e}")
        return None

def fetch_large_transactions(min_value_usd=500000):
    """
    Utilise l'API GraphQL de BitQuery pour repérer des transferts > min_value_usd.
    Ici : réseau Ethereum, sur les dernières 24h.
    """
    now = datetime.datetime.now(timezone.utc)
    start_time = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    query = """
    query ($min_value: Float!, $from_date: ISO8601DateTime!, $till_date: ISO8601DateTime!){
      ethereum(network: ethereum) {
        transfers(
          time: {since: $from_date, till: $till_date}
          amountUsd: {greater: $min_value}
        ) {
          transaction {
            hash
          }
          amount
          currency {
            symbol
          }
          amountUsd
          sender {
            address
          }
          receiver {
            address
          }
        }
      }
    }
    """

    variables = {
        "min_value": float(min_value_usd),
        "from_date": start_time,
        "till_date": end_time
    }

    url = "https://graphql.bitquery.io/"
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": BITQUERY_API_KEY
    }

    try:
        response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
        response.raise_for_status()
        data = response.json()

        transfers = data.get("data", {}).get("ethereum", {}).get("transfers", [])
        results = []
        for t in transfers:
            results.append({
                "transaction_hash": t["transaction"]["hash"],
                "amount": t["amount"],  # Montant en token
                "from_address": t["sender"]["address"],
                "to_address": t["receiver"]["address"]
            })
        return results

    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'appel API BitQuery : {e}")
        return []

def fetch_stablecoin_movements():
    """
    Exemple d'appel à l’API Etherscan pour suivre les mouvements de stablecoins.
    """
    url = ETHERSCAN_BASE_URL
    params = {
        "module": "account",
        "action": "tokentx",
        "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # ex. USDT
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc",
        "apikey": ETHERSCAN_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        transactions = data.get('result', [])
        total_value = 0
        for tx in transactions:
            pass
        result = {
            "token": "USDT",
            "transaction_count": len(transactions),
            "total_value": total_value
        }
        return result

    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'appel API Etherscan : {e}")
        return None

# --------------------------------------------------------------------
# 4. FONCTIONS D'INSERTION EN BASE DE DONNÉES
# --------------------------------------------------------------------
def insert_rss_data(connection, rss_articles):
    """
    Insère les articles RSS dans la table `rss_data`.
    """
    today = datetime.date.today()
    with connection.cursor() as cursor:
        sql = """
            INSERT INTO rss_data (date, title, link, published)
            VALUES (%s, %s, %s, %s)
        """
        for article in rss_articles:
            cursor.execute(sql, (
                today,
                article["title"],
                article["link"],
                article["published"].strftime('%Y-%m-%d %H:%M:%S') if article["published"] else None
            ))
    connection.commit()

def insert_market_sentiment(connection, sentiment):
    """
    Insère le sentiment du marché dans la table `market_sentiment`.
    """
    if not sentiment:
        return
    today = datetime.date.today()
    with connection.cursor() as cursor:
        sql = """
            INSERT INTO market_sentiment (date, positive, neutral, negative)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (
            today,
            sentiment["positive"],
            sentiment["neutral"],
            sentiment["negative"]
        ))
    connection.commit()

def insert_large_transactions(connection, big_transfers):
    """
    Insère les gros transferts (ex-Whale) dans `whale_activity`.
    """
    today = datetime.date.today()
    with connection.cursor() as cursor:
        sql = """
            INSERT INTO whale_activity (date, transaction_hash, amount, from_address, to_address)
            VALUES (%s, %s, %s, %s, %s)
        """
        for tx in big_transfers:
            cursor.execute(sql, (
                today,
                tx["transaction_hash"],
                tx["amount"],
                tx["from_address"],
                tx["to_address"]
            ))
    connection.commit()

def insert_stablecoin_movements(connection, stablecoin_data):
    """
    Insère les mouvements de stablecoins dans `stablecoin_movements`.
    """
    if not stablecoin_data:
        return
    today = datetime.date.today()
    with connection.cursor() as cursor:
        sql = """
            INSERT INTO stablecoin_movements (date, token, transaction_count, total_value)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (
            today,
            stablecoin_data["token"],
            stablecoin_data["transaction_count"],
            stablecoin_data["total_value"]
        ))
    connection.commit()

# --------------------------------------------------------------------
# 5. THÈMES SPÉCIFIQUES PAR JOUR DE LA SEMAINE
# --------------------------------------------------------------------
day_specific_topics = {
    "Monday":     ["DeFi Outlook", "Memecoins Highlights"],
    "Tuesday":    ["NFTs", "Tokenomics Insights"],
    "Wednesday":  ["Stablecoin Trends", "Regulatory News"],
    "Thursday":   ["Technical Indicators"],
    "Friday":     ["Weekly Highlights", "Market Sentiment Recap"],
    "Saturday":   ["Top Trends", "Community Highlights"],
    "Sunday":     ["Weekly Preview", "Long-Term Trends"]
}

# --------------------------------------------------------------------
# 6. FONCTION PRINCIPALE DE GÉNÉRATION DE LA STRUCTURE VIDÉO
# --------------------------------------------------------------------
def generate_video_content():
    """
    Génère la structure de la vidéo du jour :
    - Introduction (via flux RSS)
    - Daily Topics (RSS Articles, Market Sentiment, etc.)
    - Day-Specific Topics
    - Conclusion
    """
    day_of_week = datetime.datetime.today().strftime('%A')

    # 6.1 Récupération des données
    rss_articles = fetch_rss_data(CRYPTO_NEWS_RSS_URL)
    sentiment = analyze_market_sentiment()
    big_transfers = fetch_large_transactions(min_value_usd=500000)  # ex. > 500k USD
    stablecoin_data = fetch_stablecoin_movements()

    # 6.2 Connexion BDD & insertion
    connection = get_db_connection()

    if rss_articles:
        insert_rss_data(connection, rss_articles)
    if sentiment:
        insert_market_sentiment(connection, sentiment)
    if big_transfers:
        insert_large_transactions(connection, big_transfers)
    if stablecoin_data:
        insert_stablecoin_movements(connection, stablecoin_data)

    connection.close()

    # 6.3 Construction de la structure finale

    # Introduction
    introduction_text = (
        "Bienvenue dans notre mise à jour quotidienne crypto ! "
        "Aujourd'hui, nous allons explorer les derniers articles RSS, "
        "analyser le sentiment du marché et regarder les transactions importantes (whales) "
        "sur Ethereum."
    )

    # Daily Topics
    daily_topics = {
        "Top RSS Articles": [
            f"{i+1}. {art['title']} (publié le {art['published'].strftime('%Y-%m-%d %H:%M') if art['published'] else 'N/A'})"
            for i, art in enumerate(rss_articles[:3])
        ],
        "Market Sentiment": sentiment,
        "Large Transactions": [tx["transaction_hash"] for tx in big_transfers[:3]]  # Just an example
    }

    # Day-Specific Topics
    today_topics = day_specific_topics.get(day_of_week, [])
    day_specific_content = {}
    for topic in today_topics:
        day_specific_content[topic] = f"Contenu d'analyse pour {topic}..."

    # Conclusion
    conclusion_text = (
        "C'est tout pour aujourd'hui ! Merci d'avoir suivi cette analyse crypto. "
        "N'oubliez pas de vous abonner pour plus de contenu et de partager vos retours !"
    )

    video_content = {
        "Introduction": introduction_text,
        "Daily Topics": daily_topics,
        "Day-Specific Topics": day_specific_content,
        "Conclusion": conclusion_text
    }

    return video_content

# --------------------------------------------------------------------
# 7. POINT D'ENTRÉE DU SCRIPT
# --------------------------------------------------------------------
if __name__ == "__main__":
    content = generate_video_content()
    print(json.dumps(content, indent=4, ensure_ascii=False))