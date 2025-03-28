import pathlib
import unicodedata
from typing import Literal

import httpx
import pydantic

SearchModel = Literal[
    "anime_model_lovelive",  # 高级动画识别模型①
    "pre_stable",  # 高级动画识别模型②
    "anime",  # 普通动画识别模型
    "full_game_model_kira",  # 高级Gal识别模型
]

code2error = {
    17701: "图片大小过大",
    17702: "服务器繁忙，请重试",
    17703: "请求参数不正确",
    17704: "API维护中",
    17705: "图片格式不支持",
    17706: "识别无法完成（内部错误，请重试）",
    17707: "内部错误",
    17708: "图片中的人物数量超过限制",
    17709: "无法加载统计数量",
    17710: "图片验证码错误",
    17711: "无法完成识别前准备工作（请重试）",
    17712: "需要图片名称",
    17799: "不明错误发生",
}


class SearchDataCharacter(pydantic.BaseModel):
    character: str
    work: str

    def get_character_normalized(self) -> str:
        character = unicodedata.normalize("NFKC", self.character)
        character = character.replace(" ", "").split(",")[0]
        return character


class SearchData(pydantic.BaseModel):
    box: tuple[float, float, float, float] = pydantic.Field(repr=False)
    box_id: str = pydantic.Field(repr=False)
    character: list[SearchDataCharacter]


class SearchResponse(pydantic.BaseModel):
    ai: bool | None
    code: int
    data: list[SearchData] | None = None

    def code_to_error(self) -> str | None:
        if self.code == 0:
            return None
        return code2error.get(self.code) or f"未知错误代码：{self.code}"

    def unwrap_data(self) -> list[SearchData]:
        err = self.code_to_error()
        if err:
            raise ValueError(err)
        if self.data is None:
            raise ValueError("data is None")
        return self.data


def search(
    file_or_url: str,
    model: SearchModel,
    base_url: str = "https://api.animetrace.com",
    endpoint: str = "v1/search",
    is_multi: bool = True,
    ai_detect: bool = False,
):
    url = None
    file_content = None
    if file_or_url.startswith("http://") or file_or_url.startswith("https://"):
        url = file_or_url
    elif (file_path := pathlib.Path(file_or_url)).exists():
        file_content = file_path.read_bytes()
    else:
        raise ValueError("Invalid input")

    data = {
        "model": model,
        "ai_detect": ai_detect,
        "is_multi": is_multi,
    }
    if url:
        response = httpx.post(
            f"{base_url}/{endpoint}",
            data={"url": url, **data},
        )
    elif file_content:
        response = httpx.post(
            f"{base_url}/{endpoint}",
            data=data,
            files={"file": file_content},
        )
    else:
        assert False, "Not reachable"

    response.raise_for_status()
    response_model = SearchResponse.model_validate_json(response.content)
    response_model_data = response_model.unwrap_data()
    return response_model_data
