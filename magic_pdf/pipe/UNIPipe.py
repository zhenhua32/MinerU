import json

from loguru import logger

from magic_pdf.config.make_content_config import DropMode, MakeMode
from magic_pdf.data.data_reader_writer import DataWriter
from magic_pdf.libs.commons import join_path
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.pipe.AbsPipe import AbsPipe
from magic_pdf.user_api import parse_ocr_pdf, parse_union_pdf


class UNIPipe(AbsPipe):
    """主要暴露的类, 重点看一下

    Args:
        AbsPipe (_type_): _description_
    """

    def __init__(self, pdf_bytes: bytes, jso_useful_key: dict, image_writer: DataWriter, is_debug: bool = False,
                 start_page_id=0, end_page_id=None, lang=None,
                 layout_model=None, formula_enable=None, table_enable=None):
        """参数还是挺多的, 注释下

        Args:
            pdf_bytes (bytes): pdf 二进制内容
            jso_useful_key (dict): 字典, 示例数据为 {"_pdf_type": "", "model_list": []}  model_list 是模型结果
            image_writer (AbsReaderWriter): 图像写入器
            is_debug (bool, optional): 开启 debug 模式. Defaults to False.
            start_page_id (int, optional): 起始页索引. Defaults to 0.
            end_page_id (_type_, optional): 结束页索引. Defaults to None.
            lang (_type_, optional): 语言. Defaults to None.
            layout_model (_type_, optional): layout 模型. Defaults to None.
            formula_enable (_type_, optional): 是否启用公式识别. Defaults to None.
            table_enable (_type_, optional): 是否启用表格识别. Defaults to None.
        """
        self.pdf_type = jso_useful_key["_pdf_type"]
        super().__init__(pdf_bytes, jso_useful_key["model_list"], image_writer, is_debug, start_page_id, end_page_id,
                         lang, layout_model, formula_enable, table_enable)
        if len(self.model_list) == 0:
            self.input_model_is_empty = True
        else:
            self.input_model_is_empty = False

    def pipe_classify(self):
        """流程第一步, 识别 pdf 类型
        """
        self.pdf_type = AbsPipe.classify(self.pdf_bytes)

    def pipe_analyze(self):
        """流程第二步, 文档解析, 获取模型结果
        """
        # 就是只改变了一个 ocr 参数
        if self.pdf_type == self.PIP_TXT:
            self.model_list = doc_analyze(self.pdf_bytes, ocr=False,
                                          start_page_id=self.start_page_id, end_page_id=self.end_page_id,
                                          lang=self.lang, layout_model=self.layout_model,
                                          formula_enable=self.formula_enable, table_enable=self.table_enable)
        elif self.pdf_type == self.PIP_OCR:
            self.model_list = doc_analyze(self.pdf_bytes, ocr=True,
                                          start_page_id=self.start_page_id, end_page_id=self.end_page_id,
                                          lang=self.lang, layout_model=self.layout_model,
                                          formula_enable=self.formula_enable, table_enable=self.table_enable)

    def pipe_parse(self):
        """流程第三步, 获取中间结果
        """
        # 根据 pdf 类型, 调用不同的解析方法
        if self.pdf_type == self.PIP_TXT:
            self.pdf_mid_data = parse_union_pdf(self.pdf_bytes, self.model_list, self.image_writer,
                                                is_debug=self.is_debug, input_model_is_empty=self.input_model_is_empty,
                                                start_page_id=self.start_page_id, end_page_id=self.end_page_id,
                                                lang=self.lang, layout_model=self.layout_model,
                                                formula_enable=self.formula_enable, table_enable=self.table_enable)
        elif self.pdf_type == self.PIP_OCR:
            self.pdf_mid_data = parse_ocr_pdf(self.pdf_bytes, self.model_list, self.image_writer,
                                              is_debug=self.is_debug,
                                              start_page_id=self.start_page_id, end_page_id=self.end_page_id,
                                              lang=self.lang)

    def pipe_mk_uni_format(self, img_parent_path: str, drop_mode=DropMode.NONE_WITH_REASON):
        """获取 txt 格式的结果

        Args:
            img_parent_path (str): _description_
            drop_mode (_type_, optional): _description_. Defaults to DropMode.NONE_WITH_REASON.

        Returns:
            _type_: _description_
        """
        result = super().pipe_mk_uni_format(img_parent_path, drop_mode)
        logger.info('uni_pipe mk content list finished')
        return result

    def pipe_mk_markdown(self, img_parent_path: str, drop_mode=DropMode.WHOLE_PDF, md_make_mode=MakeMode.MM_MD):
        """获取 markdown 文本

        Args:
            img_parent_path (str): 图片目录
            drop_mode (_type_, optional): _description_. Defaults to DropMode.WHOLE_PDF.
            md_make_mode (_type_, optional): _description_. Defaults to MakeMode.MM_MD.

        Returns:
            _type_: _description_
        """
        result = super().pipe_mk_markdown(img_parent_path, drop_mode, md_make_mode)
        logger.info(f'uni_pipe mk {md_make_mode} finished')
        return result


if __name__ == '__main__':
    # 测试
    from magic_pdf.data.data_reader_writer import DataReader
    drw = DataReader(r'D:/project/20231108code-clean')

    pdf_file_path = r'linshixuqiu\19983-00.pdf'
    model_file_path = r'linshixuqiu\19983-00.json'
    pdf_bytes = drw.read(pdf_file_path)
    model_json_txt = drw.read(model_file_path).decode()
    model_list = json.loads(model_json_txt)
    write_path = r'D:\project\20231108code-clean\linshixuqiu\19983-00'
    img_bucket_path = 'imgs'
    img_writer = DataWriter(join_path(write_path, img_bucket_path))

    # pdf_type = UNIPipe.classify(pdf_bytes)
    # jso_useful_key = {
    #     "_pdf_type": pdf_type,
    #     "model_list": model_list
    # }

    jso_useful_key = {
        '_pdf_type': '',
        'model_list': model_list
    }
    pipe = UNIPipe(pdf_bytes, jso_useful_key, img_writer)
    pipe.pipe_classify()
    pipe.pipe_parse()
    md_content = pipe.pipe_mk_markdown(img_bucket_path)
    content_list = pipe.pipe_mk_uni_format(img_bucket_path)

    md_writer = DataWriter(write_path)
    md_writer.write_string('19983-00.md', md_content)
    md_writer.write_string('19983-00.json', json.dumps(pipe.pdf_mid_data, ensure_ascii=False, indent=4))
    md_writer.write_string('19983-00.txt', str(content_list))
