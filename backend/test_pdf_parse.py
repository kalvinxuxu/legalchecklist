"""
测试 PDF 解析
"""
import asyncio
import sys
sys.path.append('.')

from app.services.document.parser import document_parser

async def test_pdf_parse():
    file_path = r"C:\Users\kalvi\Documents\claude application\ai saas legal\backend\test_daxing.pdf"
    print(f"正在解析：{file_path}")

    try:
        result = await document_parser.parse_pdf(file_path)
        print(f"解析成功！")
        print(f"来源：{result.get('source')}")
        print(f"页数：{result.get('pages')}")
        print(f"文本长度：{len(result.get('text', ''))}")
        print(f"\n前 500 字符：")
        print(result.get('text', '')[:500])

        if 'error' in result:
            print(f"\n错误：{result.get('error')}")
    except Exception as e:
        print(f"解析失败：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pdf_parse())
