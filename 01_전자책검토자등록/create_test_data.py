import pandas as pd

# 테스트용 샘플 데이터 생성
test_data = {
    '이름': ['김철수', '이영희', '박민수', '최지영', '정대한'],
    '도서명': ['Python 프로그래밍 기초', '데이터 분석 입문서', '웹 개발 완전정복', '머신러닝 실전 가이드', 'AI와 미래사회'],
    '지메일': ['test1@gmail.com', 'test2@gmail.com', 'test3@gmail.com', 'test4@gmail.com', 'test5@gmail.com']
}

# DataFrame 생성
df = pd.DataFrame(test_data)

# 엑셀 파일로 저장
df.to_excel('test_ebook_reviewers.xlsx', index=False)

print("테스트용 엑셀 파일이 생성되었습니다: test_ebook_reviewers.xlsx")
print("\n데이터 미리보기:")
print(df)
