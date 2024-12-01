from magic_pdf.config.enums import SupportedPdfParseMethod
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.pdf_parse_union_core_v2 import pdf_parse_union


def parse_pdf_by_txt(
    pdf_bytes,
    model_list,
    imageWriter,
    start_page_id=0,
    end_page_id=None,
    debug_mode=False,
    lang=None,
):
    """解析文本类的 pdf

    Args:
        pdf_bytes (bytes): pdf 文件的二进制内容
        model_list (list): layout 模型推理结果
        imageWriter (FileBasedDataWriter): 图片写入器
        start_page_id (int, optional): 起始页. Defaults to 0.
        end_page_id (int, optional): 结束页. Defaults to None.
        debug_mode (bool, optional): 开启调试模式. Defaults to False.
        lang (str, optional): 语言. Defaults to None.

    Returns:
        _type_: _description_
    """
    dataset = PymuDocDataset(pdf_bytes)
    return pdf_parse_union(dataset,
                           model_list,
                           imageWriter,
                           SupportedPdfParseMethod.TXT,
                           start_page_id=start_page_id,
                           end_page_id=end_page_id,
                           debug_mode=debug_mode,
                           lang=lang,
                           )
