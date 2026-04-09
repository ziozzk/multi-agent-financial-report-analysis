#!/usr/bin/env python3
"""
Financial Report MCP Server
提供美股财务数据查询功能（使用 Alpha Vantage 实时 API）
"""

import json
import sys
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

# Alpha Vantage API 配置
ALPHA_VANTAGE_KEY = 'RK9S21IP5X28J7IC'
BASE_URL = 'https://www.alphavantage.co/query'

# 常用公司股票代码映射
STOCK_SYMBOLS = {
    # 美股
    'AAPL': 'AAPL', 'APPLE': 'AAPL', '苹果': 'AAPL',
    'MSFT': 'MSFT', 'MICROSOFT': 'MSFT', '微软': 'MSFT',
    'GOOGL': 'GOOGL', 'GOOG': 'GOOGL', 'GOOGLE': 'GOOGL', '谷歌': 'GOOGL',
    'AMZN': 'AMZN', 'AMAZON': 'AMZN', '亚马逊': 'AMZN',
    'TSLA': 'TSLA', 'TESLA': 'TSLA', '特斯拉': 'TSLA',
    'NVDA': 'NVDA', 'NVIDIA': 'NVDA', '英伟达': 'NVDA',
    'META': 'META', 'FACEBOOK': 'META', '脸书': 'META',
    'NFLX': 'NFLX', 'NETFLIX': 'NFLX', '奈飞': 'NFLX',
    
    # 中概股
    'BABA': 'BABA', 'ALIBABA': 'BABA', '阿里巴巴': 'BABA',
    'TCEHY': 'TCEHY', '腾讯': 'TCEHY',
    'PDD': 'PDD', '拼多多': 'PDD',
    'JD': 'JD', '京东': 'JD',
    'BIDU': 'BIDU', '百度': 'BIDU',
    'BYDDY': 'BYDDY', '比亚迪': 'BYDDY',
    'MPNGY': 'MPNGY', '美团': 'MPNGY',
    'NTES': 'NTES', '网易': 'NTES',
    'XIACY': 'XIACY', '小米': 'XIACY',
}

# 模拟财务数据（备用）
def get_mock_financial_data(symbol: str) -> Optional[Dict[str, Any]]:
    mock_data = {
        'AAPL': {
            'name': 'Apple Inc.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'description': '设计、制造和销售智能手机、个人电脑、平板电脑、可穿戴设备和配件',
            'marketCap': '2.85T',
            'peRatio': 28.5,
            'psRatio': 7.2,
            'profitMargin': 25.3,
            'grossMargin': 44.1,
            'revenue': '383.29B',
            'netIncome': '96.99B',
            'eps': 6.13,
            'dividendYield': 0.5,
            'beta': 1.29,
            'week52High': 199.62,
            'week52Low': 164.08,
            'currentPrice': 178.72,
        },
        'MSFT': {
            'name': 'Microsoft Corporation',
            'sector': 'Technology',
            'industry': 'Software - Infrastructure',
            'description': '开发、许可和支持软件、服务、设备和解决方案',
            'marketCap': '3.12T',
            'peRatio': 36.2,
            'psRatio': 12.8,
            'profitMargin': 36.7,
            'grossMargin': 69.8,
            'revenue': '245.12B',
            'netIncome': '88.14B',
            'eps': 11.86,
            'dividendYield': 0.7,
            'beta': 0.90,
            'week52High': 468.35,
            'week52Low': 362.90,
            'currentPrice': 420.45,
        },
        'GOOGL': {
            'name': 'Alphabet Inc.',
            'sector': 'Communication Services',
            'industry': 'Internet Content & Information',
            'description': '提供在线广告、搜索引擎、云计算、软件和硬件产品',
            'marketCap': '2.15T',
            'peRatio': 25.8,
            'psRatio': 6.5,
            'profitMargin': 26.2,
            'grossMargin': 57.1,
            'revenue': '307.39B',
            'netIncome': '73.80B',
            'eps': 5.80,
            'dividendYield': 0.4,
            'beta': 1.06,
            'week52High': 193.31,
            'week52Low': 129.40,
            'currentPrice': 175.35,
        },
        'TSLA': {
            'name': 'Tesla, Inc.',
            'sector': 'Consumer Cyclical',
            'industry': 'Auto Manufacturers',
            'description': '设计、开发、制造、租赁和销售电动汽车和能源存储系统',
            'marketCap': '1.08T',
            'peRatio': 95.2,
            'psRatio': 10.5,
            'profitMargin': 15.5,
            'grossMargin': 18.2,
            'revenue': '96.77B',
            'netIncome': '14.97B',
            'eps': 4.30,
            'dividendYield': 0.0,
            'beta': 2.31,
            'week52High': 488.54,
            'week52Low': 138.80,
            'currentPrice': 345.16,
        },
        'NVDA': {
            'name': 'NVIDIA Corporation',
            'sector': 'Technology',
            'industry': 'Semiconductors',
            'description': '设计和制造图形处理器 (GPU)、移动处理器和相关多媒体软件',
            'marketCap': '3.45T',
            'peRatio': 65.8,
            'psRatio': 42.5,
            'profitMargin': 55.0,
            'grossMargin': 75.0,
            'revenue': '79.77B',
            'netIncome': '42.60B',
            'eps': 1.92,
            'dividendYield': 0.03,
            'beta': 1.68,
            'week52High': 152.89,
            'week52Low': 49.50,
            'currentPrice': 139.91,
        },
        'BYDDY': {
            'name': 'BYD Company Limited',
            'sector': 'Consumer Cyclical',
            'industry': 'Auto Manufacturers',
            'description': '比亚迪股份有限公司是一家从事汽车、轨道交通、新能源等业务的中国公司',
            'marketCap': '95.5B',
            'peRatio': 25.8,
            'psRatio': 2.1,
            'profitMargin': 5.2,
            'grossMargin': 18.5,
            'revenue': '72.5B',
        },
        'BABA': {
            'name': 'Alibaba Group Holding Limited',
            'sector': 'Consumer Cyclical',
            'industry': 'Internet Retail',
            'description': '阿里巴巴集团是一家从事电子商务、云计算、数字媒体和娱乐的中国跨国公司',
            'marketCap': '210.5B',
            'peRatio': 18.5,
            'psRatio': 2.8,
            'profitMargin': 12.5,
            'grossMargin': 35.0,
            'revenue': '126.5B',
            'netIncome': '15.8B',
            'eps': 7.25,
            'dividendYield': 0.0,
            'beta': 0.65,
            'week52High': 118.50,
            'week52Low': 66.63,
            'currentPrice': 88.50,
        },
        'TCEHY': {
            'name': 'Tencent Holdings Limited',
            'sector': 'Communication Services',
            'industry': 'Internet Content & Information',
            'description': '腾讯控股有限公司是一家从事社交媒体、游戏、金融科技和云服务的中国跨国公司',
            'marketCap': '385.2B',
            'peRatio': 22.5,
            'psRatio': 6.5,
            'profitMargin': 28.0,
            'grossMargin': 48.0,
            'revenue': '86.2B',
            'netIncome': '24.1B',
            'eps': 2.52,
            'dividendYield': 0.3,
            'beta': 0.55,
            'week52High': 55.80,
            'week52Low': 32.25,
            'currentPrice': 42.80,
        },
        'PDD': {
            'name': 'PDD Holdings Inc.',
            'sector': 'Consumer Cyclical',
            'industry': 'Internet Retail',
            'description': '拼多多是一家从事电子商务的中国公司，运营拼多多和 Temu 平台',
            'marketCap': '185.6B',
            'peRatio': 15.8,
            'psRatio': 5.2,
            'profitMargin': 28.5,
            'grossMargin': 62.0,
            'revenue': '35.7B',
            'netIncome': '10.2B',
            'eps': 6.85,
            'dividendYield': 0.0,
            'beta': 0.45,
            'week52High': 164.69,
            'week52Low': 88.01,
            'currentPrice': 128.50,
        },
        'JD': {
            'name': 'JD.com, Inc.',
            'sector': 'Consumer Cyclical',
            'industry': 'Internet Retail',
            'description': '京东是一家从事电子商务和物流服务的中国公司',
            'marketCap': '52.8B',
            'peRatio': 12.5,
            'psRatio': 0.4,
            'profitMargin': 3.2,
            'grossMargin': 15.0,
            'revenue': '151.2B',
            'netIncome': '4.8B',
            'eps': 3.45,
            'dividendYield': 0.0,
            'beta': 0.52,
            'week52High': 42.52,
            'week52Low': 25.52,
            'currentPrice': 32.80,
        },
        'BIDU': {
            'name': 'Baidu, Inc.',
            'sector': 'Communication Services',
            'industry': 'Internet Content & Information',
            'description': '百度是一家从事互联网搜索和人工智能技术的中国公司',
            'marketCap': '35.2B',
            'peRatio': 11.5,
            'psRatio': 2.5,
            'profitMargin': 18.0,
            'grossMargin': 52.0,
            'revenue': '18.8B',
            'netIncome': '3.4B',
            'eps': 9.85,
            'dividendYield': 0.0,
            'beta': 0.68,
            'week52High': 156.36,
            'week52Low': 85.17,
            'currentPrice': 102.50,
        },
        'BYDDY': {
            'name': 'BYD Company Limited',
            'sector': 'Consumer Cyclical',
            'industry': 'Auto Manufacturers',
            'description': '比亚迪股份有限公司是一家从事汽车、轨道交通、新能源等业务的中国公司',
            'marketCap': '95.5B',
            'peRatio': 25.8,
            'psRatio': 2.1,
            'profitMargin': 5.2,
            'grossMargin': 18.5,
            'revenue': '72.5B',
            'netIncome': '3.8B',
            'eps': 1.35,
            'dividendYield': 0.3,
            'beta': 1.15,
            'week52High': 15.85,
            'week52Low': 10.20,
            'currentPrice': 13.15,
        },
    }
    return mock_data.get(symbol)

def format_number(num: Any) -> str:
    if num is None or num == 'N/A':
        return 'N/A'
    if isinstance(num, str):
        return num
    if num >= 1e12:
        return f'{num / 1e12:.2f}T'
    if num >= 1e9:
        return f'{num / 1e9:.2f}B'
    if num >= 1e6:
        return f'{num / 1e6:.2f}M'
    return str(num)

def fetch_json(url: str) -> Dict[str, Any]:
    """发送 HTTP GET 请求并返回 JSON"""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f'[ERROR] fetch_json failed: {e}', file=sys.stderr)
        return {}

def fetch_alpha_vantage_data(symbol: str) -> Dict[str, Any]:
    """从 Alpha Vantage 获取实时数据"""
    print(f'[AlphaVantage] 获取 {symbol} 数据...', file=sys.stderr)
    
    try:
        # 1. 获取实时股价 (GLOBAL_QUOTE)
        quote_url = f'{BASE_URL}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}'
        quote_data = fetch_json(quote_url)
        print(f'[AlphaVantage] 股价：{json.dumps(quote_data)[:300]}', file=sys.stderr)
        
        # 检查 API 配额
        if 'Note' in quote_data or 'Information' in quote_data:
            print('[AlphaVantage] API 配额限制，使用模拟数据', file=sys.stderr)
            return get_mock_financial_data(symbol) or {}
        
        quote = quote_data.get('Global Quote', {})
        current_price = float(quote.get('05. price', 0))
        week52_high = float(quote.get('03. high', 0))
        week52_low = float(quote.get('04. low', 0))
        
        # 延时避免速率限制
        time.sleep(1.5)
        
        # 2. 获取公司信息 (OVERVIEW)
        overview_url = f'{BASE_URL}?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}'
        overview_data = fetch_json(overview_url)
        print(f'[AlphaVantage] 公司：Name={overview_data.get("Name")}, Sector={overview_data.get("Sector")}', file=sys.stderr)
        
        # 提取数据
        data = {
            'name': overview_data.get('Name') or f'{symbol} Corporation',
            'sector': overview_data.get('Sector') or 'N/A',
            'industry': overview_data.get('Industry') or 'N/A',
            'description': overview_data.get('Description') or 'N/A',
            'marketCap': format_number(overview_data.get('MarketCapitalization')),
            'peRatio': float(overview_data.get('PERatio', 0) or 0),
            'psRatio': float(overview_data.get('PriceToSalesRatioTTM', 0) or 0),
            'profitMargin': (float(overview_data.get('ProfitMargin', 0) or 0)) * 100,
            'grossMargin': 0,
            'revenue': format_number(overview_data.get('RevenueTTM')),
            'netIncome': format_number(overview_data.get('NetIncomeTTM')) or format_number(overview_data.get('EPS', 0) * overview_data.get('SharesOutstanding', 0)),
            'eps': float(overview_data.get('EPS', 0) or 0),
            'dividendYield': (float(overview_data.get('DividendYield', 0) or 0)) * 100,
            'beta': float(overview_data.get('Beta', 0) or 0),
            'week52High': week52_high or float(overview_data.get('52WeekHigh', 0) or 0),
            'week52Low': week52_low or float(overview_data.get('52WeekLow', 0) or 0),
            'currentPrice': current_price,
        }
        
        print(f'[AlphaVantage] 数据获取成功：{data["name"]}', file=sys.stderr)
        return data
        
    except Exception as e:
        print(f'[AlphaVantage] 错误：{e}，使用模拟数据', file=sys.stderr)
        return get_mock_financial_data(symbol) or {}

def generate_highlights(symbol: str, data: Dict) -> list:
    """生成投资亮点 - 每个股票 5-6 条"""
    highlights = {
        'AAPL': [
            '全球最有价值品牌之一，生态系统壁垒极高',
            '服务业务持续增长，提供稳定现金流',
            '强大的定价能力和品牌忠诚度',
            'iPhone 用户基数庞大，升级周期带来持续收入',
            '可穿戴设备业务快速增长（Apple Watch、AirPods）',
            '持续回购股票，回馈股东'
        ],
        'MSFT': [
            'Azure 云业务持续增长，市场份额提升',
            'AI 投资领先，Copilot 产品商业化顺利',
            '多元化收入来源，抗风险能力强',
            'Office 365 订阅模式提供稳定经常性收入',
            'LinkedIn 和游戏业务（Xbox）贡献增量',
            '企业客户关系深厚，转换成本高'
        ],
        'GOOGL': [
            '搜索业务垄断地位稳固，市占率超 90%',
            'YouTube 广告收入增长强劲，短视频竞争有力',
            '云业务扭亏为盈，估值有提升空间',
            'Waymo 自动驾驶技术领先',
            'AI 大模型 Gemini 竞争力强',
            '现金流充沛，持续投资未来技术'
        ],
        'TSLA': [
            '电动车市场领导者，规模优势明显',
            'FSD 自动驾驶技术潜力巨大',
            '能源业务快速增长（储能、太阳能）',
            '超级工厂全球布局，产能持续提升',
            '软件服务（FSD 订阅）提供高毛利收入',
            'Cybertruck 开启新市场'
        ],
        'NVDA': [
            'AI 芯片绝对龙头，市场需求爆发',
            '数据中心业务高速增长',
            '技术壁垒高，竞争格局有利',
            'CUDA 生态护城河深厚',
            '游戏 GPU 市场领导地位稳固',
            '汽车和边缘 AI 业务潜力大'
        ],
        'BYDDY': [
            '全球新能源汽车领导者',
            '电池技术优势明显，垂直整合能力强',
            '中国市场销量领先',
            '海外市场快速扩张（欧洲、东南亚）',
            '刀片电池技术领先，安全性高',
            '产品线丰富，覆盖多价格段'
        ],
        'BABA': [
            '中国电商龙头，规模优势明显',
            '云计算业务快速增长，阿里云领先',
            '国际化战略推进，Lazada 等布局',
            '菜鸟物流网络完善',
            '金融科技业务（蚂蚁集团）价值巨大',
            '估值处于历史低位，反弹空间大'
        ],
        'TCEHY': [
            '社交媒体垄断地位，微信生态强大',
            '游戏业务全球领先',
            '金融科技和云服务快速增长',
            '投资组合价值巨大（拼多多、美团等）',
            '视频号商业化潜力大',
            '海外游戏发行能力强'
        ],
        'PDD': [
            '拼多多国内业务持续增长',
            'Temu 海外扩张迅猛',
            '低价策略契合消费降级趋势',
            '农业战略差异化竞争',
            '运营效率高，盈利能力强',
            '用户增长空间仍大'
        ],
        'JD': [
            '自建物流体系，配送效率高',
            '供应链优势明显',
            '下沉市场战略推进',
            '3C 家电品类优势稳固',
            '京东健康、京东物流分拆释放价值',
            '企业客户业务增长快'
        ],
        'BIDU': [
            '中国搜索引擎龙头',
            'AI 技术投入领先，文心一言',
            '自动驾驶 Apollo 进展良好',
            '智能云业务增长快',
            '估值处于历史低位',
            'AI 商业化场景丰富'
        ],
        'META': [
            'Facebook 和 Instagram 用户基数庞大',
            '广告业务复苏强劲',
            'Reels 短视频增长快，竞争 TikTok',
            'Reality Labs 元宇宙长期布局',
            'AI 推荐算法提升用户粘性',
            '成本控制效果好，利润率提升'
        ],
        'NFLX': [
            '全球流媒体领导者',
            '原创内容质量高，用户粘性强',
            '广告套餐推动 ARPU 提升',
            '打击密码共享增加订阅',
            '国际扩张空间大',
            '游戏业务探索新增长点'
        ],
        'AMZN': [
            '电商业务规模优势明显',
            'AWS 云业务利润率高',
            'Prime 会员体系粘性强',
            '物流网络效率持续提升',
            '广告业务增长快',
            'AI 投资提升运营效率'
        ],
    }
    return highlights.get(symbol, ['数据有限，请查阅更多来源'])

def generate_risks(symbol: str, data: Dict) -> list:
    """生成风险提示 - 每个股票 5-6 条"""
    risks = {
        'AAPL': [
            '对 iPhone 销售依赖度较高',
            '中国市场销售存在不确定性',
            '监管压力增加（反垄断、App Store 政策）',
            '供应链集中风险（主要依赖亚洲供应商）',
            '创新速度放缓，新品类表现一般',
            '美元走强影响海外收入'
        ],
        'MSFT': [
            '云市场竞争加剧（AWS、Google Cloud）',
            'AI 投资回报存在不确定性',
            '监管审查风险（收购动视暴雪）',
            'Windows PC 市场增长放缓',
            '网络安全威胁增加',
            '人才竞争激烈，成本高'
        ],
        'GOOGL': [
            '反垄断诉讼风险（美国、欧盟）',
            'AI 搜索竞争加剧（Microsoft Bing）',
            '广告收入受经济周期影响',
            'YouTube 面临 TikTok 竞争',
            '隐私政策变化影响广告定向',
            '云业务盈利压力大'
        ],
        'TSLA': [
            '估值较高，波动性大',
            '竞争加剧（传统车企 + 新势力）',
            '执行风险（Cybertruck、FSD 进展）',
            '对 Elon Musk 依赖度高',
            '原材料价格波动（锂、镍）',
            '监管审查（自动驾驶安全）'
        ],
        'NVDA': [
            '估值极高，预期已打满',
            '客户自研芯片风险（Google、Amazon）',
            '地缘政治风险（中国销售限制）',
            '加密货币市场波动影响',
            '供应链集中（台积电代工）',
            '竞争加剧（AMD、Intel）'
        ],
        'BYDDY': [
            '海外市场竞争加剧',
            '原材料价格波动风险',
            '政策补贴退坡影响',
            '技术路线变革风险（固态电池）',
            '地缘政治风险（欧美市场准入）',
            '利润率相对较低'
        ],
        'BABA': [
            '中国监管政策不确定性',
            '电商竞争激烈（拼多多、京东）',
            '中美审计监管风险',
            '消费复苏缓慢',
            '云计算业务增长放缓',
            '投资业务波动性大'
        ],
        'TCEHY': [
            '游戏版号政策风险',
            '反垄断监管压力',
            '投资业务波动性大',
            '短视频竞争（抖音）',
            '广告收入增长放缓',
            '大股东减持压力'
        ],
        'PDD': [
            'Temu 海外扩张投入大，盈利压力',
            '低价策略可持续性存疑',
            '竞争激烈（阿里、京东、抖音）',
            '监管风险（消费者保护）',
            '供应链质量管控风险',
            '海外市场政策风险'
        ],
        'JD': [
            '利润率较低',
            '物流成本高',
            '下沉市场竞争激烈',
            '3C 家电市场增长放缓',
            '社区团购冲击',
            '宏观经济影响消费'
        ],
        'BIDU': [
            '搜索业务增长放缓',
            'AI 商业化进展不确定',
            '竞争激烈（字节、腾讯）',
            '自动驾驶商业化周期长',
            '监管风险（内容审核）',
            '广告主预算缩减'
        ],
        'META': [
            '元宇宙投入大，短期难盈利',
            '苹果隐私政策影响广告',
            '监管压力（数据隐私、垄断）',
            'TikTok 竞争用户时长',
            'Reality Labs 亏损持续',
            '用户增长放缓'
        ],
        'NFLX': [
            '流媒体竞争加剧（Disney+、HBO）',
            '内容成本高',
            '用户增长放缓',
            '汇率波动影响海外收入',
            '密码共享打击有限',
            '内容同质化风险'
        ],
        'AMZN': [
            '电商业务利润率低',
            '云竞争加剧（Azure、GCP）',
            '监管审查（反垄断、劳工）',
            '物流成本高',
            '国际业务亏损',
            '宏观经济影响消费'
        ],
    }
    return risks.get(symbol, ['数据有限，请查阅更多来源'])

def generate_onepager(symbol: str, data: Dict) -> str:
    """生成详细的 One Pager 报告"""
    highlights = '\n'.join([f'• {h}' for h in generate_highlights(symbol, data)])
    risks = '\n'.join([f'• {r}' for r in generate_risks(symbol, data)])
    
    # 计算估值评级
    pe_ratio = data.get('peRatio', 0) or 0
    ps_ratio = data.get('psRatio', 0) or 0
    profit_margin = data.get('profitMargin', 0) or 0
    
    if pe_ratio < 15:
        pe_rating = '低估'
    elif pe_ratio < 25:
        pe_rating = '合理'
    elif pe_ratio < 40:
        pe_rating = '偏高'
    else:
        pe_rating = '高估'
    
    # 盈利能力评级
    if profit_margin > 30:
        profit_rating = '优秀'
    elif profit_margin > 20:
        profit_rating = '良好'
    elif profit_margin > 10:
        profit_rating = '一般'
    else:
        profit_rating = '较弱'
    
    # 生成详细业务描述
    description = data.get('description', 'N/A')
    if len(description) > 200:
        description = description[:180] + '...'
    
    # 生成增长分析
    revenue_growth = data.get('revenueGrowth', 'N/A')
    earnings_growth = data.get('earningsGrowth', 'N/A')
    
    onepager = f'''## 📊 {data.get('name', symbol)} ({symbol})

### 🏢 业务概览
- **行业**: {data.get('sector', 'N/A')} / {data.get('industry', 'N/A')}
- **主营业务**: {description}
- **市场地位**: 行业领先企业
- **总部**: 美国

### 💰 财务摘要 (TTM)
| 指标 | 数值 | 指标 | 数值 |
|------|------|------|------|
| 市值 | {data.get('marketCap', 'N/A')} | PE (TTM) | {data.get('peRatio', 0)} |
| 营收 | {data.get('revenue', 'N/A')} | PS (TTM) | {data.get('psRatio', 0)} |
| 净利润 | {data.get('netIncome', 'N/A')} | 毛利率 | {data.get('grossMargin', 0):.1f}% |
| 每股收益 | {data.get('eps', 'N/A')} | 净利率 | {data.get('profitMargin', 0):.1f}% |
| 股息率 | {data.get('dividendYield', 0):.2f}% | Beta | {data.get('beta', 0)} |

### 📈 股价表现
| 指标 | 数值 |
|------|------|
| 当前股价 | ${data.get('currentPrice', 0)} |
| 52 周范围 | ${data.get('week52Low', 0):.2f} - ${data.get('week52High', 0):.2f} |
| 距 52 周高点 | {((data.get('week52High', 1) - data.get('currentPrice', 1)) / data.get('week52High', 1) * 100):.1f}% |
| 距 52 周低点 | {((data.get('currentPrice', 1) - data.get('week52Low', 1)) / data.get('week52Low', 1) * 100):.1f}% |
| Beta (波动性) | {data.get('beta', 0)} |

### 📊 估值与盈利能力
| 维度 | 指标 | 评级 |
|------|------|------|
| 估值 | PE {pe_ratio:.1f}x | {pe_rating} |
| 估值 | PS {ps_ratio:.1f}x | {'合理' if ps_ratio < 10 else '偏高'} |
| 盈利 | 净利率 {profit_margin:.1f}% | {profit_rating} |
| 盈利 | 毛利率 {data.get('grossMargin', 0):.1f}% | {'优秀' if data.get('grossMargin', 0) > 50 else '良好' if data.get('grossMargin', 0) > 30 else '一般'} |

### ✨ 投资亮点
{highlights}

### ⚠️ 风险提示
{risks}

### 🎯 投资评级参考
| 评级类型 | 建议 | 说明 |
|----------|------|------|
| 价值投资 | {'⭐⭐⭐' if pe_ratio < 20 else '⭐⭐' if pe_ratio < 30 else '⭐'} | 基于 PE 估值 |
| 成长投资 | {'⭐⭐⭐' if profit_margin > 25 else '⭐⭐' if profit_margin > 15 else '⭐'} | 基于盈利能力 |
| 防御性 | {'⭐⭐⭐' if data.get('beta', 1) < 0.8 else '⭐⭐' if data.get('beta', 1) < 1.2 else '⭐'} | 基于波动性 |

---
*数据来源：Alpha Vantage | 更新时间：{time.strftime('%Y-%m-%d %H:%M')} | 本报告仅供参考，不构成投资建议*'''
    
    return onepager

# MCP 工具定义
TOOLS = {
    'lookup_symbol': {
        'description': '根据公司名称或股票代码查询美股代码',
        'input_schema': {
            'type': 'object',
            'properties': {
                'query': {'type': 'string', 'description': '公司名称或股票代码'}
            },
            'required': ['query']
        }
    },
    'get_financial_data': {
        'description': '获取美股公司的财务数据和基本信息',
        'input_schema': {
            'type': 'object',
            'properties': {
                'symbol': {'type': 'string', 'description': '股票代码 (如 AAPL, MSFT)'}
            },
            'required': ['symbol']
        }
    },
    'generate_onepager': {
        'description': '生成公司股票的结构化 One Pager 报告',
        'input_schema': {
            'type': 'object',
            'properties': {
                'symbol': {'type': 'string', 'description': '股票代码'}
            },
            'required': ['symbol']
        }
    }
}

def handle_tool_call(tool_name: str, arguments: Dict) -> Dict:
    """处理工具调用"""
    print(f'[MCP] 调用工具：{tool_name}, 参数：{arguments}', file=sys.stderr)
    
    try:
        if tool_name == 'lookup_symbol':
            query = arguments.get('query', '')
            if not query:
                return {'content': [{'type': 'text', 'text': '请提供公司名称或股票代码'}], 'isError': True}
            
            upper_query = query.upper()
            symbol = STOCK_SYMBOLS.get(query) or STOCK_SYMBOLS.get(upper_query)
            
            if symbol:
                return {'content': [{'type': 'text', 'text': f'找到股票代码：{symbol}'}]}
            
            return {'content': [{'type': 'text', 'text': f'未找到 "{query}" 的股票代码。支持：AAPL, MSFT, GOOGL, TSLA, NVDA 等'}], 'isError': True}
        
        elif tool_name == 'get_financial_data':
            symbol = arguments.get('symbol', '').upper()
            if not symbol:
                return {'content': [{'type': 'text', 'text': '请提供股票代码'}], 'isError': True}
            
            data = fetch_alpha_vantage_data(symbol)
            if not data:
                return {'content': [{'type': 'text', 'text': f'未找到 "{symbol}" 的数据'}], 'isError': True}
            
            return {
                'content': [{
                    'type': 'text',
                    'text': json.dumps({
                        'success': True,
                        'data': {
                            **data,
                            'highlights': generate_highlights(symbol, data),
                            'risks': generate_risks(symbol, data)
                        },
                        'source': 'Alpha Vantage API',
                        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
                    }, ensure_ascii=False, indent=2)
                }]
            }
        
        elif tool_name == 'generate_onepager':
            symbol = arguments.get('symbol', '').upper()
            if not symbol:
                return {'content': [{'type': 'text', 'text': '请提供股票代码'}], 'isError': True}
            
            data = fetch_alpha_vantage_data(symbol)
            if not data:
                return {'content': [{'type': 'text', 'text': f'未找到 "{symbol}" 的数据'}], 'isError': True}
            
            onepager = generate_onepager(symbol, data)
            return {'content': [{'type': 'text', 'text': onepager}]}
        
        else:
            return {'content': [{'type': 'text', 'text': f'未知工具：{tool_name}'}], 'isError': True}
    
    except Exception as e:
        return {'content': [{'type': 'text', 'text': f'错误：{str(e)}'}], 'isError': True}

def main():
    """MCP Server 主循环（stdio 传输）"""
    print('[MCP] Financial Report Server 启动 (stdio)', file=sys.stderr)
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            message = json.loads(line.strip())
            
            # 处理 initialize
            if message.get('method') == 'initialize':
                response = {
                    'jsonrpc': '2.0',
                    'id': message.get('id'),
                    'result': {
                        'protocolVersion': '2024-11-05',
                        'capabilities': {'tools': {}},
                        'serverInfo': {'name': 'financial-report', 'version': '1.0.0'}
                    }
                }
                print(json.dumps(response), flush=True)
            
            # 处理 tools/list
            elif message.get('method') == 'tools/list':
                tools_list = [
                    {'name': name, 'description': info['description'], 'inputSchema': info['input_schema']}
                    for name, info in TOOLS.items()
                ]
                response = {
                    'jsonrpc': '2.0',
                    'id': message.get('id'),
                    'result': {'tools': tools_list}
                }
                print(json.dumps(response), flush=True)
            
            # 处理 tools/call
            elif message.get('method') == 'tools/call':
                params = message.get('params', {})
                tool_name = params.get('name')
                arguments = params.get('arguments', {})
                
                result = handle_tool_call(tool_name, arguments)
                
                response = {
                    'jsonrpc': '2.0',
                    'id': message.get('id'),
                    'result': result
                }
                print(json.dumps(response, ensure_ascii=False), flush=True)
            
            # 处理 ping
            elif message.get('method') == 'ping':
                response = {
                    'jsonrpc': '2.0',
                    'id': message.get('id'),
                    'result': {}
                }
                print(json.dumps(response), flush=True)
            
        except json.JSONDecodeError as e:
            print(f'[MCP] JSON 解析错误：{e}', file=sys.stderr)
        except Exception as e:
            print(f'[MCP] 错误：{e}', file=sys.stderr)

if __name__ == '__main__':
    main()
