from typing import Optional, Literal, Union
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, status
from app.core.constants import PAGE_SIZE
from app.dtos.community_dtos.Community_list_response import CursorListResponse
from app.dtos.community_dtos.community_request import PostCreateRequest, StudyPostCreate, FreePostCreate, \
    SharePostCreate, PostUpdateAny
from app.dtos.community_dtos.community_response import PostDetailResponse, StudyPostResponse, FreePostResponse, \
    SharePostResponse
from app.services.community_services.community_common_service import service_delete_post_by_post_id
from app.services.community_services.community_get_service import service_list_posts_cursor
from app.services.community_services.post_detail_service import service_get_post_detail
from app.services.community_services import community_post_service as post_svc
from app.services.community_services.post_update_service import service_update_post

router = APIRouter(prefix="/api/v1/community", tags=["Community · Post"]) # 모든 엔드포인트 앞에 공통 접두사(/api/v1/community)가 붙고 문서에는 "Community · Post" 그룹으로 보임

RequestCategory = Literal["all", "study", "free", "share"] # 허용된 문자열만 받도록 제한 / 타이핑,오타를 줄이고 문서에도 선택지로 노출
SearchIn = Literal["title", "content", "title_content", "author"]

@router.get("/post/list", response_model=CursorListResponse)  # 목록 조회 라우터 / response_model로 응답 모양 고정
async def list_posts_cursor(
    category: RequestCategory = Query("all", description="all | study | free | share"), # 어떤 카테고리를 볼지, Literal로 오타 방지함
    q: Optional[str] = Query(None), # 검색어
    search_in: SearchIn = Query("title_content", description="title | content | title_content | author"), # 검색 대상 필드를 지정함
    cursor: Optional[int] = Query(None), # 무한스크롤의 다음 페이지 기준점
    limit: int = Query(PAGE_SIZE, ge=1, le=50), # 한번에 몇개까지(최소 1개에서 최대 50) PAGE_SIZE로 20개
    author_id: Optional[int] = Query(None), # 특정 작성자 글만
    date_from: Optional[datetime] = Query(None), # 기간 필터
    date_to: Optional[datetime] = Query(None),
    badge: Optional[Literal["모집중","모집완료"]] = Query(None, description="study 전용 배지 필터"), # 스터디 전용 배지로 걸러 볼 수 있음
):
    return await service_list_posts_cursor( # 라우터는 파라미터만 정리해서 서비스에 위임 / 라우터는 얇고, 로직은 서비스에 모여서 재사용/테스트가 쉬움
        category=category,
        q=q, search_in=search_in,
        cursor=cursor, limit=limit,
        author_id=author_id, date_from=date_from, date_to=date_to,
        badge=badge,
    )

@router.get("/post/{post_id:int}", response_model=PostDetailResponse) # 게시글 상세 조회 라우터 / response_model로 응답 고정
async def get_post_detail(post_id: int):
    data = await service_get_post_detail(post_id) # 디비에서 글을 찾아오는 비동기 함수
    if not data: # 조건문으로 게시글이 없으면 에러코드 반환
        raise HTTPException(404, "Post not found")
    return data

@router.post("/post", response_model=PostDetailResponse, status_code=status.HTTP_201_CREATED) # 게시글 생성 라우터 / 201로 성공 명시
async def create_post(body: PostCreateRequest, user :int): # body = 요청 dto로 유효성 자동 검사 / user: int = 작성자 명시 (get_current_user) 변경 예정
    try:
        if isinstance(body, StudyPostCreate): # PostCreateRequest가 Union으로 각 카테고리 중 하나로 파싱되면 실제 객체 타입을 보고 해당 서비스로 분기
            return await post_svc.service_create_study_post( # 스터디 모집 게시글에는 모집기간, 스터디기간, 최대인원 과 같은 추가 필드가 있기에 카테고리 별 서로 다른dto/서비스를 호출
                user_id=user,
                title=body.title,
                content=body.content,
                recruit_start=body.recruit_start,
                recruit_end=body.recruit_end,
                study_start=body.study_start,
                study_end=body.study_end,
                max_member=body.max_member,
            )
        elif isinstance(body, FreePostCreate):
            return await post_svc.service_create_free_post(
                user_id=user,
                title=body.title,
                content=body.content,
            )
        elif isinstance(body, SharePostCreate):
            return await post_svc.service_create_share_post(
                user_id=user,
                title=body.title,
                content=body.content,
            )
        else:
            raise HTTPException(400, "Unsupported category")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch(
    "/post/{post_id:int}", # 게시글 부분수정 라우터 /
    response_model=Union[StudyPostResponse, FreePostResponse, SharePostResponse],
)
async def patch_post(
        post_id: int,
        body: PostUpdateAny,
        user: int,  # 실제 운영에선: current_user = Depends(get_current_user); user_id = current_user.id
):
    payload = body.model_dump(exclude_unset=True) # 요청에서 보내지 않은 필드는 제외해서 수정 / 부분 업데이트의 핵심임
    if not payload: # 빈 patch를 사전에 차단(아무것도 수정을 안함)
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        return await service_update_post(post_id=post_id, user_id=user, payload=payload)
    except HTTPException:
        raise
    except Exception as e:
        # 서비스 내부에서 이미 적절히 HTTPException을 던지므로
        # 예기치 못한 에러만 400으로 래핑
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/post/{post_id}")
async def delete_post(post_id: int, user: int):
    return await service_delete_post_by_post_id(post_id=post_id, user_id=user)