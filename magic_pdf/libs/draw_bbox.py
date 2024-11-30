from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.libs.commons import fitz  # PyMuPDF
from magic_pdf.libs.Constants import CROSS_PAGE
from magic_pdf.libs.ocr_content_type import BlockType, CategoryId, ContentType
from magic_pdf.model.magic_model import MagicModel


def draw_bbox_without_number(i: int, bbox_list: list, page, rgb_config: list, fill_config: bool):
    """画框

    Args:
        i (int): 页数索引
        bbox_list (list): bbox 列表
        page (Document): Document page
        rgb_config (list): 颜色
        fill_config (bool): 是否填充
    """
    # 颜色需要转换成 0-1 之间的小数
    new_rgb = []
    for item in rgb_config:
        item = float(item) / 255
        new_rgb.append(item)
    page_data = bbox_list[i]  # 第 i 页的 bbox 列表
    for bbox in page_data:
        x0, y0, x1, y1 = bbox
        # 定义矩形, 左上, 右下
        rect_coords = fitz.Rect(x0, y0, x1, y1)  # Define the rectangle
        if fill_config:
            # 填充版本
            page.draw_rect(
                rect_coords,
                color=None,
                fill=new_rgb,
                fill_opacity=0.3,
                width=0.5,
                overlay=True,
            )  # Draw the rectangle
        else:
            # 非填充版本
            page.draw_rect(
                rect_coords,
                color=new_rgb,
                fill=None,
                fill_opacity=1,
                width=0.5,
                overlay=True,
            )  # Draw the rectangle


def draw_bbox_with_number(i: int, bbox_list: list, page, rgb_config: list, fill_config: bool, draw_bbox=True):
    """画框, 附带序号

    Args:
        i (_type_): _description_
        bbox_list (_type_): _description_
        page (_type_): _description_
        rgb_config (_type_): _description_
        fill_config (_type_): _description_
        draw_bbox (bool, optional): _description_. Defaults to True.
    """
    new_rgb = []
    for item in rgb_config:
        item = float(item) / 255
        new_rgb.append(item)
    page_data = bbox_list[i]
    for j, bbox in enumerate(page_data):
        x0, y0, x1, y1 = bbox
        rect_coords = fitz.Rect(x0, y0, x1, y1)  # Define the rectangle
        if draw_bbox:
            if fill_config:
                page.draw_rect(
                    rect_coords,
                    color=None,
                    fill=new_rgb,
                    fill_opacity=0.3,
                    width=0.5,
                    overlay=True,
                )  # Draw the rectangle
            else:
                page.draw_rect(
                    rect_coords,
                    color=new_rgb,
                    fill=None,
                    fill_opacity=1,
                    width=0.5,
                    overlay=True,
                )  # Draw the rectangle
        # 加个数字
        page.insert_text(
            (x1 + 2, y0 + 10), str(j + 1), fontsize=10, color=new_rgb
        )  # Insert the index in the top left corner of the rectangle


def draw_layout_bbox(pdf_info: list, pdf_bytes: bytes, out_path: str, filename: str):
    """画布局框，附带排序结果

    Args:
        pdf_info (list): pipe.pipe_parse 调用后返回的结果
        pdf_bytes (bytes): pdf 文件的二进制数据
        out_path (str): 输出目录
        filename (str): 文件名
    """
    dropped_bbox_list = []
    tables_list, tables_body_list = [], []
    tables_caption_list, tables_footnote_list = [], []
    imgs_list, imgs_body_list, imgs_caption_list = [], [], []
    imgs_footnote_list = []
    titles_list = []
    texts_list = []
    interequations_list = []
    lists_list = []
    indexs_list = []
    for page in pdf_info:
        # 按页面处理

        # 初始化
        page_dropped_list = []
        tables, tables_body, tables_caption, tables_footnote = [], [], [], []
        imgs, imgs_body, imgs_caption, imgs_footnote = [], [], [], []
        titles = []
        texts = []
        interequations = []
        lists = []
        indices = []

        # 丢弃的表格的 bbox
        for dropped_bbox in page['discarded_blocks']:
            page_dropped_list.append(dropped_bbox['bbox'])
        dropped_bbox_list.append(page_dropped_list)

        # 逐个处理每个 block. para_blocks 是分段后的结果
        for block in page['para_blocks']:
            bbox = block['bbox']
            if block['type'] == BlockType.Table:
                tables.append(bbox)
                for nested_block in block['blocks']:
                    # 处理内嵌表格, 一个表格可能由 表格体, 表格标题, 表格脚注 组成
                    bbox = nested_block['bbox']
                    if nested_block['type'] == BlockType.TableBody:
                        tables_body.append(bbox)
                    elif nested_block['type'] == BlockType.TableCaption:
                        tables_caption.append(bbox)
                    elif nested_block['type'] == BlockType.TableFootnote:
                        tables_footnote.append(bbox)
            elif block['type'] == BlockType.Image:
                imgs.append(bbox)
                for nested_block in block['blocks']:
                    # 图像也是同样的处理方式
                    bbox = nested_block['bbox']
                    if nested_block['type'] == BlockType.ImageBody:
                        imgs_body.append(bbox)
                    elif nested_block['type'] == BlockType.ImageCaption:
                        imgs_caption.append(bbox)
                    elif nested_block['type'] == BlockType.ImageFootnote:
                        imgs_footnote.append(bbox)
            elif block['type'] == BlockType.Title:
                titles.append(bbox)
            elif block['type'] == BlockType.Text:
                texts.append(bbox)
            elif block['type'] == BlockType.InterlineEquation:  # 行间公式块
                interequations.append(bbox)
            elif block['type'] == BlockType.List:
                lists.append(bbox)
            elif block['type'] == BlockType.Index:
                indices.append(bbox)

        tables_list.append(tables)
        tables_body_list.append(tables_body)
        tables_caption_list.append(tables_caption)
        tables_footnote_list.append(tables_footnote)
        imgs_list.append(imgs)
        imgs_body_list.append(imgs_body)
        imgs_caption_list.append(imgs_caption)
        imgs_footnote_list.append(imgs_footnote)
        titles_list.append(titles)
        texts_list.append(texts)
        interequations_list.append(interequations)
        lists_list.append(lists)
        indexs_list.append(indices)

    # 这个是按顺序全部加进来, 前面是按类型分开的
    layout_bbox_list = []

    table_type_order = {
        'table_caption': 1,
        'table_body': 2,
        'table_footnote': 3
    }
    for page in pdf_info:
        page_block_list = []
        for block in page['para_blocks']:
            if block['type'] in [
                BlockType.Text,
                BlockType.Title,
                BlockType.InterlineEquation,
                BlockType.List,
                BlockType.Index,
            ]:
                bbox = block['bbox']
                page_block_list.append(bbox)
            elif block['type'] in [BlockType.Image]:
                for sub_block in block['blocks']:
                    bbox = sub_block['bbox']
                    page_block_list.append(bbox)
            elif block['type'] in [BlockType.Table]:
                sorted_blocks = sorted(block['blocks'], key=lambda x: table_type_order[x['type']])
                for sub_block in sorted_blocks:
                    bbox = sub_block['bbox']
                    page_block_list.append(bbox)

        layout_bbox_list.append(page_block_list)

    pdf_docs = fitz.open('pdf', pdf_bytes)

    for i, page in enumerate(pdf_docs):

        draw_bbox_without_number(i, dropped_bbox_list, page, [158, 158, 158], True)
        # draw_bbox_without_number(i, tables_list, page, [153, 153, 0], True)  # color !
        draw_bbox_without_number(i, tables_body_list, page, [204, 204, 0], True)
        draw_bbox_without_number(i, tables_caption_list, page, [255, 255, 102], True)
        draw_bbox_without_number(i, tables_footnote_list, page, [229, 255, 204], True)
        # draw_bbox_without_number(i, imgs_list, page, [51, 102, 0], True)
        draw_bbox_without_number(i, imgs_body_list, page, [153, 255, 51], True)
        draw_bbox_without_number(i, imgs_caption_list, page, [102, 178, 255], True)
        draw_bbox_without_number(i, imgs_footnote_list, page, [255, 178, 102], True),
        draw_bbox_without_number(i, titles_list, page, [102, 102, 255], True)
        draw_bbox_without_number(i, texts_list, page, [153, 0, 76], True)
        draw_bbox_without_number(i, interequations_list, page, [0, 255, 0], True)
        draw_bbox_without_number(i, lists_list, page, [40, 169, 92], True)
        draw_bbox_without_number(i, indexs_list, page, [40, 169, 92], True)

        # 这个是标记数字的
        draw_bbox_with_number(
            i, layout_bbox_list, page, [255, 0, 0], False, draw_bbox=False
        )

    # Save the PDF
    pdf_docs.save(f'{out_path}/{filename}_layout.pdf')


def draw_span_bbox(pdf_info, pdf_bytes, out_path, filename):
    text_list = []
    inline_equation_list = []
    interline_equation_list = []
    image_list = []
    table_list = []
    dropped_list = []
    next_page_text_list = []
    next_page_inline_equation_list = []

    def get_span_info(span):
        if span['type'] == ContentType.Text:
            if span.get(CROSS_PAGE, False):
                next_page_text_list.append(span['bbox'])
            else:
                page_text_list.append(span['bbox'])
        elif span['type'] == ContentType.InlineEquation:
            if span.get(CROSS_PAGE, False):
                next_page_inline_equation_list.append(span['bbox'])
            else:
                page_inline_equation_list.append(span['bbox'])
        elif span['type'] == ContentType.InterlineEquation:
            page_interline_equation_list.append(span['bbox'])
        elif span['type'] == ContentType.Image:
            page_image_list.append(span['bbox'])
        elif span['type'] == ContentType.Table:
            page_table_list.append(span['bbox'])

    for page in pdf_info:
        page_text_list = []
        page_inline_equation_list = []
        page_interline_equation_list = []
        page_image_list = []
        page_table_list = []
        page_dropped_list = []

        # 将跨页的span放到移动到下一页的列表中
        if len(next_page_text_list) > 0:
            page_text_list.extend(next_page_text_list)
            next_page_text_list.clear()
        if len(next_page_inline_equation_list) > 0:
            page_inline_equation_list.extend(next_page_inline_equation_list)
            next_page_inline_equation_list.clear()

        # 构造dropped_list
        for block in page['discarded_blocks']:
            if block['type'] == BlockType.Discarded:
                for line in block['lines']:
                    for span in line['spans']:
                        page_dropped_list.append(span['bbox'])
        dropped_list.append(page_dropped_list)
        # 构造其余useful_list
        # for block in page['para_blocks']:  # span直接用分段合并前的结果就可以
        for block in page['preproc_blocks']:
            if block['type'] in [
                BlockType.Text,
                BlockType.Title,
                BlockType.InterlineEquation,
                BlockType.List,
                BlockType.Index,
            ]:
                for line in block['lines']:
                    for span in line['spans']:
                        get_span_info(span)
            elif block['type'] in [BlockType.Image, BlockType.Table]:
                for sub_block in block['blocks']:
                    for line in sub_block['lines']:
                        for span in line['spans']:
                            get_span_info(span)
        text_list.append(page_text_list)
        inline_equation_list.append(page_inline_equation_list)
        interline_equation_list.append(page_interline_equation_list)
        image_list.append(page_image_list)
        table_list.append(page_table_list)
    pdf_docs = fitz.open('pdf', pdf_bytes)
    for i, page in enumerate(pdf_docs):
        # 获取当前页面的数据
        draw_bbox_without_number(i, text_list, page, [255, 0, 0], False)
        draw_bbox_without_number(i, inline_equation_list, page, [0, 255, 0], False)
        draw_bbox_without_number(i, interline_equation_list, page, [0, 0, 255], False)
        draw_bbox_without_number(i, image_list, page, [255, 204, 0], False)
        draw_bbox_without_number(i, table_list, page, [204, 0, 255], False)
        draw_bbox_without_number(i, dropped_list, page, [158, 158, 158], False)

    # Save the PDF
    pdf_docs.save(f'{out_path}/{filename}_spans.pdf')


def draw_model_bbox(model_list: list, pdf_bytes: bytes, out_path: str, filename: str):
    """画模型结果的框

    Args:
        model_list (list): layout 模型结果
        pdf_bytes (bytes): pdf 文件的二进制数据
        out_path (str): 输出目录
        filename (str): 文件名
    """
    dropped_bbox_list = []
    tables_body_list, tables_caption_list, tables_footnote_list = [], [], []
    imgs_body_list, imgs_caption_list, imgs_footnote_list = [], [], []
    titles_list = []
    texts_list = []
    interequations_list = []
    pdf_docs = fitz.open('pdf', pdf_bytes)
    magic_model = MagicModel(model_list, PymuDocDataset(pdf_bytes))
    for i in range(len(model_list)):
        # 按页处理, i 是页数索引
        page_dropped_list = []
        tables_body, tables_caption, tables_footnote = [], [], []
        imgs_body, imgs_caption, imgs_footnote = [], [], []
        titles = []
        texts = []
        interequations = []
        page_info = magic_model.get_model_list(i)
        # 获取到 page_info 后和上面的 draw_layout_bbox 处理方式一样
        layout_dets = page_info['layout_dets']
        for layout_det in layout_dets:
            bbox = layout_det['bbox']
            if layout_det['category_id'] == CategoryId.Text:
                texts.append(bbox)
            elif layout_det['category_id'] == CategoryId.Title:
                titles.append(bbox)
            elif layout_det['category_id'] == CategoryId.TableBody:
                tables_body.append(bbox)
            elif layout_det['category_id'] == CategoryId.TableCaption:
                tables_caption.append(bbox)
            elif layout_det['category_id'] == CategoryId.TableFootnote:
                tables_footnote.append(bbox)
            elif layout_det['category_id'] == CategoryId.ImageBody:
                imgs_body.append(bbox)
            elif layout_det['category_id'] == CategoryId.ImageCaption:
                imgs_caption.append(bbox)
            elif layout_det['category_id'] == CategoryId.InterlineEquation_YOLO:
                interequations.append(bbox)
            elif layout_det['category_id'] == CategoryId.Abandon:
                page_dropped_list.append(bbox)
            elif layout_det['category_id'] == CategoryId.ImageFootnote:
                imgs_footnote.append(bbox)

        tables_body_list.append(tables_body)
        tables_caption_list.append(tables_caption)
        tables_footnote_list.append(tables_footnote)
        imgs_body_list.append(imgs_body)
        imgs_caption_list.append(imgs_caption)
        titles_list.append(titles)
        texts_list.append(texts)
        interequations_list.append(interequations)
        dropped_bbox_list.append(page_dropped_list)
        imgs_footnote_list.append(imgs_footnote)

    for i, page in enumerate(pdf_docs):
        draw_bbox_with_number(
            i, dropped_bbox_list, page, [158, 158, 158], True
        )  # color !
        draw_bbox_with_number(i, tables_body_list, page, [204, 204, 0], True)
        draw_bbox_with_number(i, tables_caption_list, page, [255, 255, 102], True)
        draw_bbox_with_number(i, tables_footnote_list, page, [229, 255, 204], True)
        draw_bbox_with_number(i, imgs_body_list, page, [153, 255, 51], True)
        draw_bbox_with_number(i, imgs_caption_list, page, [102, 178, 255], True)
        draw_bbox_with_number(i, imgs_footnote_list, page, [255, 178, 102], True)
        draw_bbox_with_number(i, titles_list, page, [102, 102, 255], True)
        draw_bbox_with_number(i, texts_list, page, [153, 0, 76], True)
        draw_bbox_with_number(i, interequations_list, page, [0, 255, 0], True)

    # Save the PDF
    pdf_docs.save(f'{out_path}/{filename}_model.pdf')


def draw_line_sort_bbox(pdf_info, pdf_bytes, out_path, filename):
    layout_bbox_list = []

    for page in pdf_info:
        page_line_list = []
        for block in page['preproc_blocks']:
            if block['type'] in [BlockType.Text, BlockType.Title, BlockType.InterlineEquation]:
                for line in block['lines']:
                    bbox = line['bbox']
                    index = line['index']
                    page_line_list.append({'index': index, 'bbox': bbox})
            if block['type'] in [BlockType.Image, BlockType.Table]:
                for sub_block in block['blocks']:
                    if sub_block['type'] in [BlockType.ImageBody, BlockType.TableBody]:
                        if len(sub_block['virtual_lines']) > 0 and sub_block['virtual_lines'][0].get('index', None) is not None:
                            for line in sub_block['virtual_lines']:
                                bbox = line['bbox']
                                index = line['index']
                                page_line_list.append({'index': index, 'bbox': bbox})
                        else:
                            for line in sub_block['lines']:
                                bbox = line['bbox']
                                index = line['index']
                                page_line_list.append({'index': index, 'bbox': bbox})
                    elif sub_block['type'] in [BlockType.ImageCaption, BlockType.TableCaption, BlockType.ImageFootnote, BlockType.TableFootnote]:
                        for line in sub_block['lines']:
                            bbox = line['bbox']
                            index = line['index']
                            page_line_list.append({'index': index, 'bbox': bbox})
        sorted_bboxes = sorted(page_line_list, key=lambda x: x['index'])
        layout_bbox_list.append(sorted_bbox['bbox'] for sorted_bbox in sorted_bboxes)
    pdf_docs = fitz.open('pdf', pdf_bytes)
    for i, page in enumerate(pdf_docs):
        draw_bbox_with_number(i, layout_bbox_list, page, [255, 0, 0], False)

    pdf_docs.save(f'{out_path}/{filename}_line_sort.pdf')


def draw_layout_sort_bbox(pdf_info, pdf_bytes, out_path, filename):
    layout_bbox_list = []

    for page in pdf_info:
        page_block_list = []
        for block in page['para_blocks']:
            bbox = block['bbox']
            page_block_list.append(bbox)
        layout_bbox_list.append(page_block_list)
    pdf_docs = fitz.open('pdf', pdf_bytes)
    for i, page in enumerate(pdf_docs):
        draw_bbox_with_number(i, layout_bbox_list, page, [255, 0, 0], False)

    pdf_docs.save(f'{out_path}/{filename}_layout_sort.pdf')
