// 检查用户是否已登录
function checkLoginStatus() {
    eel.check_password_set()(function(password_set) {
        if (!password_set) {
            window.location.href = 'init.html';
            return;
        }

        const isLoggedIn = localStorage.getItem('isLoggedIn');
        if (!isLoggedIn) {
            window.location.href = 'index.html';
            return;
        }

        // 登录验证通过，加载句子列表
        loadSentences();
    });
}

// 加载句子列表
function loadSentences() {
    const sentenceListElement = document.getElementById('sentenceList');

    eel.get_all_sentences()(function(response) {
        if (response.status === 'success') {
            const sentences = response.sentences;

            if (sentences.length === 0) {
                sentenceListElement.innerHTML = '<p class="message" style="color: #fff;font-size: 18px;">这里什么都没有呐 _(:3 」∠ )_</p>';
                return;
            }

            // 清空列表
            sentenceListElement.innerHTML = '';

            // 添加句子到列表
            sentences.forEach(sentence => {
                const sentenceItem = document.createElement('div');
                sentenceItem.className = 'sentence-item';

                sentenceItem.innerHTML = `
                    <div class="sentence-content">${sentence.content}</div>
                    <div class="sentence-meta">
                        <span>来源: ${sentence.source}</span>
                        <span>作者: ${sentence.author}</span>
                    </div>
                    <div class="sentence-meta">
                        <span>分类: ${sentence.category}</span>
                        <span>添加时间: ${new Date(sentence.created_at).toLocaleString()}</span>
                    </div>
                    <div class="sentence-actions">
                        <button class="btn-action btn-edit" onclick="editSentence(${sentence.id})">编辑</button>
                        <button class="btn-action btn-delete" onclick="deleteSentence(${sentence.id})">删除</button>
                    </div>
                `;

                sentenceListElement.appendChild(sentenceItem);
            });
        } else {
            sentenceListElement.innerHTML = `<p class="message" style="color: red;">${response.message}</p>`;
        }
    });
}

// 编辑句子
function editSentence(id) {
    // 获取句子详情
    eel.get_sentence_by_id(id)(function(response) {
        if (response.status === 'success') {
            const sentence = response.data;
            // 填充表单
            document.getElementById('editId').value = sentence.id;
            document.getElementById('editSource').value = sentence.source;
            document.getElementById('editContent').value = sentence.content;
            document.getElementById('editAuthor').value = sentence.author;
            document.getElementById('editCategory').value = sentence.category;
            // 显示模态框
            document.getElementById('editModal').style.display = 'block';
        } else {
            showToastFromResponse(response);
        }
    });
}

// 关闭模态框
function closeModal() {
    document.getElementById('editModal').style.display = 'none';
}

// 点击模态框外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('editModal');
    if (event.target === modal) {
        closeModal();
    }
}

// 保存编辑后的句子（带AI复核）
function saveEditedSentence() {
    const id = document.getElementById('editId').value;
    const source = document.getElementById('editSource').value;
    const content = document.getElementById('editContent').value;
    const author = document.getElementById('editAuthor').value;
    const category = document.getElementById('editCategory').value;

    // 简单验证
    if (!content.trim()) {
        showToast('句子内容不能为空', 'error');
        return;
    }

    // 保存待审核的编辑数据
    const editData = {
        id: id,
        source: source,
        content: content,
        author: author,
        category: category,
        is_edit: true  // 标记这是编辑操作
    };

    // 保存到待审核数据并跳转到处理页面
    eel.save_edit_for_review(editData)(function(response) {
        if (response.status === 'success') {
            closeModal();
            // 跳转到处理页面进行AI复核
            window.location.href = 'processing.html?action=edit_review';
        } else {
            showToastFromResponse(response);
        }
    });
}

// 删除句子
function deleteSentence(id) {
    if (confirm('确定要删除这个句子吗？')) {
        eel.delete_sentence(id)(function(response) {
            if (response.status === 'success') {
                showToastFromResponse(response);
                // 重新加载句子列表
                loadSentences();
            } else {
                showToastFromResponse(response);
            }
        });
    }
}

// 页面加载时检查登录状态
document.addEventListener('DOMContentLoaded', checkLoginStatus);