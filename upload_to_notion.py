import os
from notion_client import Client
import re
import ssl
import httpx

def parse_markdown_to_notion_blocks(content):
    """마크다운 내용을 노션 블록으로 변환"""
    
    blocks = []
    lines = content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
            
        # 제목 처리 (# ## ### 등)
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            title = line.lstrip('# ').strip()
            
            if level == 1:
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": title}}]
                    }
                })
            elif level == 2:
                blocks.append({
                    "object": "block",
                    "type": "heading_2", 
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": title}}]
                    }
                })
            elif level >= 3:
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": title}}]
                    }
                })
        
        # 코드 블록 처리
        elif line.startswith('```'):
            code_content = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_content.append(lines[i])
                i += 1
            
            if code_content:
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": '\n'.join(code_content)}}],
                        "language": "plain text"
                    }
                })
        
        # 목록 처리 (- 또는 * 로 시작)
        elif line.startswith('- ') or line.startswith('* '):
            list_items = []
            while i < len(lines) and (lines[i].strip().startswith('- ') or lines[i].strip().startswith('* ')):
                item_text = lines[i].strip()[2:].strip()
                list_items.append(item_text)
                i += 1
            i -= 1  # 마지막에 i가 하나 더 증가하므로 보정
            
            for item in list_items:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": item}}]
                    }
                })
        
        # 번호 목록 처리 (1. 2. 등으로 시작)
        elif re.match(r'^\d+\.\s', line):
            numbered_items = []
            while i < len(lines) and re.match(r'^\d+\.\s', lines[i].strip()):
                item_text = re.sub(r'^\d+\.\s', '', lines[i].strip())
                numbered_items.append(item_text)
                i += 1
            i -= 1
            
            for item in numbered_items:
                blocks.append({
                    "object": "block", 
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": item}}]
                    }
                })
        
        # 인용문 처리 (> 로 시작)
        elif line.startswith('>'):
            quote_text = line[1:].strip()
            blocks.append({
                "object": "block",
                "type": "quote",
                "quote": {
                    "rich_text": [{"type": "text", "text": {"content": quote_text}}]
                }
            })
        
        # 구분선 처리 (--- 등)
        elif line.startswith('---'):
            blocks.append({
                "object": "block",
                "type": "divider",
                "divider": {}
            })
        
        # 일반 텍스트 처리
        else:
            # 텍스트가 너무 길면 자르기 (노션 제한)
            if len(line) > 2000:
                line = line[:1997] + "..."
            
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line}}]
                }
            })
        
        i += 1
    
    return blocks

def upload_to_notion():
    """노션에 문서 업로드"""
    
    print("🔗 노션 API 연결 및 문서 업로드 시작")
    print("=" * 50)
    
    # 노션 클라이언트 초기화
    NOTION_TOKEN = "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"
    PAGE_ID = "21c31382e0a280c587b5f2763dad8d36"
    
    try:
        # SSL 검증 우회를 위한 httpx 클라이언트 설정
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        client = httpx.Client(verify=False)
        notion = Client(auth=NOTION_TOKEN, client=client)
        print("✅ 노션 API 연결 성공")
        
        # 1. 프로젝트 설명서 업로드
        print("\n📋 1. 프로젝트 설명서 업로드 중...")
        
        with open('프로젝트_설명서_비전문가용.md', 'r', encoding='utf-8') as f:
            content1 = f.read()
        
        # 메인 설명서 페이지 생성
        main_page = notion.pages.create(
            parent={"page_id": PAGE_ID},
            properties={
                "title": {
                    "title": [
                        {
                            "type": "text",
                            "text": {
                                "content": "협업 후기 텍스트 분석 자동화 프로젝트 설명서"
                            }
                        }
                    ]
                }
            }
        )
        
        print(f"✅ 메인 페이지 생성 완료: {main_page['id']}")
        
        # 설명서 내용을 블록으로 변환하여 추가
        blocks1 = parse_markdown_to_notion_blocks(content1)
        
        # 블록을 100개씩 나누어 추가 (노션 API 제한)
        for i in range(0, len(blocks1), 100):
            chunk = blocks1[i:i+100]
            notion.blocks.children.append(
                block_id=main_page['id'],
                children=chunk
            )
            print(f"  📝 블록 {i+1}-{min(i+100, len(blocks1))} 추가 완료")
        
        print(f"✅ 설명서 업로드 완료 (총 {len(blocks1)}개 블록)")
        
        # 2. FAQ 문서 업로드
        print("\n❓ 2. FAQ 문서 업로드 중...")
        
        with open('FAQ_비전문가용.md', 'r', encoding='utf-8') as f:
            content2 = f.read()
        
        # FAQ 페이지 생성
        faq_page = notion.pages.create(
            parent={"page_id": PAGE_ID},
            properties={
                "title": {
                    "title": [
                        {
                            "type": "text",
                            "text": {
                                "content": "협업 후기 분석 자동화 프로젝트 FAQ"
                            }
                        }
                    ]
                }
            }
        )
        
        print(f"✅ FAQ 페이지 생성 완료: {faq_page['id']}")
        
        # FAQ 내용을 블록으로 변환하여 추가
        blocks2 = parse_markdown_to_notion_blocks(content2)
        
        for i in range(0, len(blocks2), 100):
            chunk = blocks2[i:i+100]
            notion.blocks.children.append(
                block_id=faq_page['id'],
                children=chunk
            )
            print(f"  ❓ 블록 {i+1}-{min(i+100, len(blocks2))} 추가 완료")
        
        print(f"✅ FAQ 업로드 완료 (총 {len(blocks2)}개 블록)")
        
        # 3. 프로젝트 요약 페이지 생성
        print("\n📊 3. 프로젝트 요약 페이지 생성 중...")
        
        summary_page = notion.pages.create(
            parent={"page_id": PAGE_ID},
            properties={
                "title": {
                    "title": [
                        {
                            "type": "text",
                            "text": {
                                "content": "프로젝트 요약 및 핵심 성과"
                            }
                        }
                    ]
                }
            }
        )
        
        # 요약 내용 생성
        summary_blocks = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": "📊 프로젝트 핵심 성과"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "🎯 처리 완료: 협업 후기 200건 AI 자동 분석"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph", 
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "💰 비용 절감: 99% (3,147만원 → 30만원)"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "⚡ 시간 단축: 131일 → 30분 (99.8% 단축)"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "📈 ROI: 381% (1년 기준)"}}]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "🔍 주요 분석 결과"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "감정 분포: 긍정 37.5%, 부정 31.0%, 중립 26.5%"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "7개 주요 그룹 패턴 발견 (클러스터링)"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "57개 유사 피드백 쌍 식별 (중복 이슈 후보)"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "부문별/부서별 상세 분석 완료"}}]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "📁 생성된 결과물"}}]
                }
            },
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "협업후기_분석결과_클러스터링_최종_상위200건.xlsx"}}]
                }
            },
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "5개 시트: 분석결과, 클러스터요약, 유사피드백쌍, 부문별분석, 부서별분석"}}]
                }
            },
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "8개 신규 분석 컬럼 추가 (감정, 키워드, 클러스터 등)"}}]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "🚀 향후 계획"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "전체 20,982건 데이터 확장 처리"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "실시간 대시보드 구축"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": "다른 부서/분야로 확산 적용"}}]
                }
            }
        ]
        
        notion.blocks.children.append(
            block_id=summary_page['id'],
            children=summary_blocks
        )
        
        print(f"✅ 프로젝트 요약 페이지 생성 완료")
        
        # 4. 최종 결과 출력
        print(f"\n🎉 노션 업로드 완료!")
        print(f"📋 생성된 페이지들:")
        print(f"  1. 프로젝트 설명서: https://notion.so/{main_page['id'].replace('-', '')}")
        print(f"  2. FAQ: https://notion.so/{faq_page['id'].replace('-', '')}")
        print(f"  3. 프로젝트 요약: https://notion.so/{summary_page['id'].replace('-', '')}")
        
        return {
            'main_page': main_page['id'],
            'faq_page': faq_page['id'], 
            'summary_page': summary_page['id']
        }
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = upload_to_notion()
    
    if result:
        print(f"\n{'='*60}")
        print("🎯 노션 페이지 활용 가이드:")
        print("1. 상사 보고용: 프로젝트 요약 페이지 활용")
        print("2. 상세 설명: 프로젝트 설명서 페이지 참조")
        print("3. 질문 대응: FAQ 페이지로 사전 답변")
        print("4. 팀 공유: 전체 팀원에게 노션 페이지 링크 공유")