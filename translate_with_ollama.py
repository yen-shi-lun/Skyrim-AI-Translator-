
import xml.etree.ElementTree as ET
import requests
import json
import os
import sys
from tqdm import tqdm
import time
import re

# ================= 設定區 =================
# 您的 Ollama 模型名稱
OLLAMA_MODEL = "gemma3:4b" 

# Ollama API URL
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# 翻譯提示詞 (Prompt)
SYSTEM_PROMPT = """
你是一個專業的《上古卷軸 V：天際》繁體中文翻譯助手。
請將提供的英文遊戲文本翻譯成台灣習慣的繁體中文。
規則：
1. 輸出完整的繁體中文句子。
2. 如果原文是「中英夾雜」的（例如 '轉過去 again'），請根據語意將英文部分也翻譯出來，整合成通順的中文（例如 '再次轉過去'）。
3. 保留所有特殊標籤和變數，例如 <mag>, <Global=Val>, [ ... ] 等，不要翻譯或修改它們。
4. 不要解釋，只輸出翻譯後的結果。
"""
# =========================================

def translate_text(text, model=OLLAMA_MODEL):
    if not text or text.strip() == "":
        return text
        
    # [修改點] 移除 "已含中文就跳過" 的邏輯，改為由主程式判斷是否包含英文

    payload = {
        "model": model,
        "prompt": f"{SYSTEM_PROMPT}\n\n原文：{text}\n譯文：",
        "stream": False,
        "options": {
            "temperature": 0.3
        }
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        translated = result.get("response", "").strip()
        
        if "<think>" in translated:
            translated = re.sub(r'<think>.*?</think>', '', translated, flags=re.DOTALL).strip()
        
        if translated.startswith('"') and translated.endswith('"'):
            translated = translated[1:-1]
            
        # [修改點] 簡單日誌，顯示處理了甚麼
        # print(f" 處理: {text[:20]}... -> {translated[:20]}...") 
        return translated
    except Exception as e:
        print(f"\n[錯誤] 翻譯失敗: {e}")
        return text

def has_english_characters(text):
    if not text:
        return False
    # 檢查是否包含 a-z 或 A-Z，但忽略 XML 標籤或變數 (簡單判斷)
    # 這裡直接檢查是否有英文字母，因為正常中文翻譯不該有英文單字
    # 但要小心 <br> 或 <alias=Player> 這種
    # 我們做一個簡單過濾：移除 <...> 和 [...] 後，看還有沒有英文
    
    clean_text = re.sub(r'<.*?>', '', text) # 移除 <...>
    clean_text = re.sub(r'\[.*?\]', '', clean_text) # 移除 [...]
    
    return bool(re.search(r'[a-zA-Z]', clean_text))

def process_xml(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"錯誤：找不到檔案 {input_path}")
        return

    print(f"正在讀取 XML: {input_path}")
    try:
        tree = ET.parse(input_path)
        root = tree.getroot()
        
        strings = root.findall(".//String")
        total_strings = len(strings)
        print(f"共找到 {total_strings} 個字串。開始使用 Ollama ({OLLAMA_MODEL}) 修復與翻譯...")
        print("注意：這將會重新翻譯所有包含殘留英文的句子。")

        # 使用 tqdm 顯示進度條
        for string_node in tqdm(strings, total=total_strings, unit="str"):
            dest_node = string_node.find("Dest")
            source_node = string_node.find("Source")
            
            if dest_node is not None and source_node is not None:
                original_text = source_node.text
                current_dest = dest_node.text
                
                # [核心修改邏輯]
                # 需要翻譯的情況：
                # 1. 目前譯文(Dest)是空的
                # 2. 目前譯文跟原文(Source)完全一樣
                # 3. 目前譯文包含英文字母（且不在標籤內），表示是「中英夾雜」或「未完全翻譯」
                
                should_translate = False
                if not current_dest: 
                    should_translate = True
                elif current_dest == original_text:
                    should_translate = True
                elif has_english_characters(current_dest):
                    should_translate = True
                
                if should_translate and original_text:
                    # 注意：我們將 'original_text' (純英文原文) 傳給 AI
                    # 讓 AI 根據純英文原文重新產生完整的中文句子，而不是去修補那個爛掉的中文
                    trans = translate_text(original_text)
                    dest_node.text = trans

        print(f"\n翻譯完成！正在儲存到 {output_path} ...")
        tree.write(output_path, encoding="UTF-8", xml_declaration=True)
        print("檔案已儲存。")
        
    except ET.ParseError:
        print("錯誤：XML 解析失敗，請確認檔案格式正確。")
    except Exception as e:
        print(f"發生未預期的錯誤：{e}")

if __name__ == "__main__":
    print("=== Skyrim Mod 本地 AI 翻譯工具 (中英夾雜修復版) ===")
    
    # 預設路徑
    default_input = r"D:\game\xTranslator-313-1-6-0-1727874549\_xTranslator\UserPrefs\SkyrimSE\xazPrisonOverhaulPatched_chinese_english.xml"
    
    input_file = input(f"請輸入 XML 檔案路徑 (預設為上一次的檔案): ").strip()
    if not input_file:
        input_file = default_input
        
    # 去除路徑可能包含的引號
    input_file = input_file.strip('"')

    output_file = input_file.replace(".xml", "_Ollama_AI_Fixed.xml")
    
    print(f"將儲存為: {output_file}")
    print(f"使用模型: {OLLAMA_MODEL}")
    print("請確保 Ollama 已經在背景執行！")
    input("按 Enter 開始翻譯...")
    
    process_xml(input_file, output_file)
    input("按 Enter 結束...")
