// static/script.js

// 显示通知函数
function showNotification(message, isError = false) {
    var notification = document.createElement('div');
    notification.className = `notification ${isError ? 'error' : 'success'}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.classList.add('fade-out');
        notification.remove();
    }, 3000); // 通知显示 3 秒后自动消失
}


const jsonPathSpan = document.getElementById('json-path');
function fileExists(filePath) {
    try {
        const xhr = new XMLHttpRequest();
        xhr.open('HEAD', filePath, false); // 设置为同步请求
        xhr.send();

        if (xhr.status >= 200 && xhr.status < 300) {
            return true; // 文件存在
        } else {
            return false; // 文件不存在
        }
    } catch (error) {
        console.error(`检查文件是否存在时出错: ${error}`);
        return false; // 请求失败时返回 false
    }
}

console.log(fileExists('/check_file/static/data.json'))

if (Object.keys(jsonData).length !== 0)
    {data=jsonData}
else {
    if (!fileExists(jsonPathSpan.textContent)) {
        jsonPathSpan.textContent='/check_file/static/data.json';
        }
    

    fetch(jsonPathSpan.textContent)
    .then(response => {
        if (!response.ok) {
            throw new Error('网络响应异常');
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            console.error('服务器返回错误:', data.error);
            showNotification('服务器错误: ' + data.error, true);
        } else {
            initializeTabs(data);
        }
    })
    .catch(error => {
        console.error('加载 JSON 数据失败:', error);
        showNotification('加载 JSON 数据失败: ' + error, true);
    });
}
console.log(jsonPathSpan.textContent);



// 绑定复制路径和打开文件夹按钮的事件
document.addEventListener('DOMContentLoaded', function() {
    const copyJsonPathBtn = document.getElementById('copy-json-path');
    const openJsonFolderBtn = document.getElementById('open-json-folder');
    const jsonPathSpan = document.getElementById('json-path');


    // 复制 JSON 文件路径
    if (copyJsonPathBtn) {
        copyJsonPathBtn.addEventListener('click', async function() {
        const path = jsonPathSpan.textContent;  
        await copyToClipBoard(path)
        });
    }

    // 打开 JSON 文件所在文件夹
    if (openJsonFolderBtn) {
        openJsonFolderBtn.addEventListener('click', function() {
            const path = jsonPathSpan.textContent;
            // window.location.href = `webcallexplorer:${path}`;
            open_path(path)
        });
    }

    // 为所有带有 data-path 属性的复制按钮添加事件监听
    document.querySelectorAll('.action-button[data-path]').forEach(button => {
        button.addEventListener('click', async function() {
            const pathToCopy = this.getAttribute('data-path');
            const action = this.getAttribute('data-action');
            console.log('action:', action);
            if (action === 'copy') await copyToClipBoard(pathToCopy)
            else {
                open_path(pathToCopy)
            }
        });
    });
});

async function copyToClipBoard(path){
    const textArea = document.createElement('textarea');
    textArea.value = jsonPathSpan.textContent;
    document.body.appendChild(textArea);
    textArea.select();
    console.log(textArea.value);
    try {
        document.execCommand('copy');
        showNotification('execCommand方法路径已复制到剪贴板');
    } catch (err) {
        showNotification('复制失败，请手动复制', true);
    }
    document.body.removeChild(textArea);
}

async function open_path(path){
    buttonData={
        localPath : path,
        actionType : 'open_path'
    }
    console.log("发送消息:", buttonData);
    window.parent.postMessage(
        { 
            action: "buttonClicked", 
            message: "Hello from B!",
            buttonData: buttonData  // 包含按钮属性的字典
        }, 
        `http://${SERVER_IP}:7500`
    );
}

// 初始化标签页和内容
function initializeTabs(data) {
    console.log(data);
    if (typeof data !== 'object' || !Array.isArray(data)) {
        data=JSON.parse(data);
    }
    const tabsContainer = document.getElementById('tabs');
    const contentsContainer = document.getElementById('tab-contents');

    // 清空现有的标签和内容
    tabsContainer.innerHTML = '';
    contentsContainer.innerHTML = '';

    data.forEach((item, index) => {
        // 创建标签按钮
        const tabButton = document.createElement('button');
        tabButton.className = 'tab-button';
        if (item.has_issue) {
            tabButton.classList.add('has-issue');
        }
        tabButton.textContent = item.tab_name;
        tabButton.setAttribute('data-index', index);
        tabButton.addEventListener('click', () => {
            setActiveTab(index);
        });
        tabsContainer.appendChild(tabButton);

        // 创建标签内容
        const tabContent = document.createElement('div');
        tabContent.className = 'tab-content';
        tabContent.setAttribute('data-index', index);

        if (item.error) {
            const errorMsg = document.createElement('p');
            errorMsg.className = 'error';
            errorMsg.textContent = '错误: ' + item.error;
            tabContent.appendChild(errorMsg);
        } else {
            // 创建表格
            const table = document.createElement('table');
            table.id = `main-table-${index}`;
            table.innerHTML = `
                <thead>
                    <tr>
                        <th>几何名称</th>
                        <th>面数</th>
                        <th>面集名称</th>
                        <th>面索引</th>
                    </tr>
                </thead>
                <tbody>
                </tbody>
            `;
            const tbody = table.querySelector('tbody');

            // 填充表格内容
            item.table_data.forEach(rowData => {
                const row = document.createElement('tr');
                if (rowData.has_issue) {
                    row.classList.add('row-issue');
                }

                ['geometry_name', 'num_faces', 'faceset_name', 'face_indices'].forEach(key => {
                    const td = document.createElement('td');
                    td.textContent = rowData[key];
                    row.appendChild(td);
                });

                tbody.appendChild(row);
            });

            tabContent.appendChild(table);

            // 元数据部分
            const metaDataDiv = document.createElement('div');
            metaDataDiv.className = 'meta-data';

            const mayaShotFile = item.meta_data?.maya_shot_file || '';
            const mayaAssetFile = item.meta_data?.maya_asset_file || '';
            const abcPath = item.abc_path || '';

            const shotFileDiv = createPathInfoDiv('Maya 镜头文件', mayaShotFile);
            const assetFileDiv = createPathInfoDiv('Maya 资产文件', mayaAssetFile);
            const abcPathDiv = createPathInfoDiv('abc 文件路径', abcPath);

            metaDataDiv.appendChild(shotFileDiv);
            metaDataDiv.appendChild(assetFileDiv);
            metaDataDiv.appendChild(abcPathDiv);

            tabContent.appendChild(metaDataDiv);
        }

        contentsContainer.appendChild(tabContent);
    });

    // 激活第一个标签
    setActiveTab(0);
}

// 设置活动标签页
function setActiveTab(index) {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(btn => btn.classList.remove('active'));
    tabContents.forEach(content => content.classList.remove('active'));

    const activeButton = document.querySelector(`.tab-button[data-index="${index}"]`);
    const activeContent = document.querySelector(`.tab-content[data-index="${index}"]`);

    if (activeButton && activeContent) {
        activeButton.classList.add('active');
        activeContent.classList.add('active');
    }
}

// 创建路径信息部分，包括复制路径和打开文件夹按钮
function createPathInfoDiv(label, path) {
    const container = document.createElement('div');
    container.className = 'path-info';

    // 复制路径按钮
    const copyButton = document.createElement('button');
    copyButton.textContent = '复制路径';
    copyButton.disabled = !path; // 如果路径为空，则禁用按钮
    copyButton.className = 'action-button copy-button';
    copyButton.setAttribute('data-path', path);
    copyButton.setAttribute('data-action', 'copy');
    container.appendChild(copyButton);

    // 打开文件夹按钮
    const openButton = document.createElement('button');
    openButton.textContent = '打开文件夹';
    openButton.disabled = !path;
    openButton.className = 'action-button open-button';
    openButton.setAttribute('data-path', path);
    openButton.setAttribute('data-action', 'open');
    container.appendChild(openButton);

    // 标签
    const labelElement = document.createElement('span');
    labelElement.textContent = `${label}: `;
    container.appendChild(labelElement);

    // 路径文本
    const pathElement = document.createElement('span');
    pathElement.textContent = path || '(未定义)';
    pathElement.className = 'path-value';
    container.appendChild(pathElement);

    return container;
}


initializeTabs(data)