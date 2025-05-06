import enum
import pathlib
import unicodedata

import httpx
import pydantic


class SearchModel(str, enum.Enum):
    anime = "anime"
    """低精度动画模型(编号: gochiusa)"""
    pre_stable = "pre_stable"
    """①高精度动画模型(编号: aqours)"""
    anime_model_lovelive = "anime_model_lovelive"
    """②高精度动画模型(编号: lovelive)"""
    full_game_model_kira = "full_game_model_kira"
    """③GalGame模型(编号: kira)"""


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
    17720: "识别成功",
    17721: "服务器正常运行中",
    17722: "图片下载失败",
    17723: "未指定 Content-Length",
    17724: "不是图片文件或未指定",
    17725: "未指定图片",
    17726: "JSON 不接受包含文件",
    17727: "Base64 格式错误",
    17728: "已达到本次使用上限",
    17729: "未找到选择的模型",
    17730: "检测 AI 图片失败",
    17731: "服务利用人数过多，请重试",
    17732: "已过期",
    17733: "反馈成功",
    17734: "反馈失败",
    17735: "反馈识别效果成功",
    17736: "验证码错误",
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
    file_or_url_or_base64: str,
    model: SearchModel | str,
    base_url: str = "https://api.animetrace.com",
    endpoint: str = "v1/search",
    is_multi: bool = True,
    ai_detect: bool = False,
):
    url = None
    file_content = None
    base64_content = None

    if isinstance(model, SearchModel):
        model = model.value

    if file_or_url_or_base64.startswith(("http://", "https://")):
        url = file_or_url_or_base64
    elif (file_path := pathlib.Path(file_or_url_or_base64)).exists():
        file_path = pathlib.Path(file_or_url_or_base64)
        if not file_path.exists():
            raise ValueError(f"File not found: {file_or_url_or_base64}")
        file_content = file_path.read_bytes()
    else:
        base64_content = file_or_url_or_base64

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
    elif base64_content:
        response = httpx.post(
            f"{base_url}/{endpoint}",
            data={"base64": base64_content, **data},
        )
    else:
        raise ValueError("No valid input provided")

    response.raise_for_status()
    response_model = SearchResponse.model_validate_json(response.content)
    response_model_data = response_model.unwrap_data()
    return response_model_data
