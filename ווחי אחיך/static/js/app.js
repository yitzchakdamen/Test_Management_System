document.addEventListener('DOMContentLoaded', function() {
    // בדיקה שהדף נטען בהצלחה
    console.log('Family tree app initialized');
    
    // אלמנטים בממשק
    const searchBtn = document.getElementById('searchBtn');
    const resetSearch = document.getElementById('resetSearch');
    const searchInput = document.getElementById('firstName');
    const resultsList = document.getElementById('resultsList');
    const familyTree = document.getElementById('familyTree');
    const personModal = document.getElementById('personModal');
    const closeModal = document.querySelector('.close-modal');
    const personInfo = document.getElementById('personInfo');
    const zoomInBtn = document.getElementById('zoomIn');
    const zoomOutBtn = document.getElementById('zoomOut');
    const resetViewBtn = document.getElementById('resetView');

    // בדיקה שכל האלמנטים קיימים
    if (!searchBtn || !resetSearch || !resultsList || !familyTree) {
        console.error('One or more critical elements are missing from the DOM');
        return;
    }

    // משתנים גלובליים
    let currentTreeData = null;
    let currentPersonId = null;
    let svg, treeLayout, zoomListener;

    // מאזינים לאירועים
    searchBtn.addEventListener('click', searchPeople);
    resetSearch.addEventListener('click', resetSearchFields);
    closeModal.addEventListener('click', () => personModal.style.display = 'none');
    window.addEventListener('click', (e) => {
        if (e.target === personModal) personModal.style.display = 'none';
    });
    
    if (zoomInBtn) zoomInBtn.addEventListener('click', zoomIn);
    if (zoomOutBtn) zoomOutBtn.addEventListener('click', zoomOut);
    if (resetViewBtn) resetViewBtn.addEventListener('click', resetView);

    // פונקציית איפוס שדות חיפוש
    function resetSearchFields() {
        document.getElementById('firstName').value = '';
        document.getElementById('lastName').value = '';
        document.getElementById('city').value = '';
        document.getElementById('phone').value = '';
        resultsList.innerHTML = '';
    }

    // פונקציית חיפוש אנשים
    async function searchPeople() {
        const firstName = document.getElementById('firstName').value.trim();
        const lastName = document.getElementById('lastName').value.trim();
        const city = document.getElementById('city').value.trim();
        const phone = document.getElementById('phone').value.trim();

        // בדיקה שיש לפחות שדה חיפוש אחד מלא
        if (!firstName && !lastName && !city && !phone) {
            alert('אנא מלא לפחות שדה חיפוש אחד');
            return;
        }

        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    first_name: firstName,
                    last_name: lastName,
                    city: city,
                    phone: phone
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const people = await response.json();
            displaySearchResults(people);
        } catch (error) {
            console.error('Error searching people:', error);
            alert('אירעה שגיאה בחיפוש: ' + error.message);
        }
    }

    // הצגת תוצאות חיפוש
    function displaySearchResults(people) {
        resultsList.innerHTML = '';
        
        if (!people || people.length === 0) {
            resultsList.innerHTML = '<p class="no-results">לא נמצאו תוצאות</p>';
            return;
        }

        // מיון התוצאות לפי שם משפחה ואז שם פרטי
        people.sort((a, b) => {
            if (a.last_name < b.last_name) return -1;
            if (a.last_name > b.last_name) return 1;
            return a.first_name.localeCompare(b.first_name);
        });

        people.forEach(person => {
            if (!person.id) {
                console.warn('Person missing ID:', person);
                return;
            }

            const personCard = document.createElement('div');
            personCard.className = 'person-card';
            personCard.innerHTML = `
                <h3>${person.title || ''} ${person.first_name} ${person.last_name}</h3>
                <p>${person.city || 'לא צוין יישוב'} | 
                   טלפון: ${person.phone || 'לא צוין'} | 
                   נייד: ${person.mobile || 'לא צוין'}</p>
            `;
            personCard.addEventListener('click', () => {
                if (person.id) {
                    loadFamilyTree(person.id);
                } else {
                    console.error('Attempted to load family tree for person without ID');
                }
            });
            resultsList.appendChild(personCard);
        });
    }

    // טעינת עץ משפחה
    async function loadFamilyTree(personId) {
        if (!personId) {
            console.error('No person ID provided to loadFamilyTree');
            return;
        }

        currentPersonId = personId;
        
        try {
            const response = await fetch(`/family/${personId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const familyData = await response.json();
            if (!familyData || !familyData.main_person) {
                throw new Error('Invalid family data received');
            }
            
            currentTreeData = familyData;
            showPersonDetails(familyData.main_person);
            createFamilyTree(familyData);
        } catch (error) {
            console.error('Error loading family tree:', error);
            alert('אירעה שגיאה בטעינת עץ המשפחה: ' + error.message);
        }
    }

    // יצירת עץ משפחה עם D3.js
    function createFamilyTree(data) {
        if (!data || !data.main_person) {
            console.error('Invalid data for family tree');
            return;
        }

        // נקה את העץ הקודם
        familyTree.innerHTML = '';
        
        // הגדר מימדים
        const width = familyTree.clientWidth;
        const height = familyTree.clientHeight;
        const margin = {top: 40, right: 90, bottom: 50, left: 90};
        
        // צור מבנה היררכי לעץ
        const root = buildHierarchy(data);
        
        // הגדר את פריסת העץ
        treeLayout = d3.tree().size([width - margin.left - margin.right, height - margin.top - margin.bottom]);
        
        // צור את ה-SVG
        svg = d3.select('#familyTree').append('svg')
            .attr('width', width)
            .attr('height', height)
            .append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);
        
        // הוסף אפשרות זום
        zoomListener = d3.zoom()
            .scaleExtent([0.5, 3])
            .on('zoom', zoomed);
            
        d3.select('#familyTree svg').call(zoomListener);
        
        // צייר את העץ
        update(root);
        
        function update(source) {
            // חישוב המיקומים של כל הצמתים
            const treeData = treeLayout(root);
            
            // מצא את כל הצמתים
            const nodes = treeData.descendants();
            
            // מצא את כל הקישורים
            const links = treeData.descendants().slice(1);
            
            // צייר את הקישורים
            svg.selectAll('.link')
                .data(links)
                .enter().append('path')
                .attr('class', 'link')
                .attr('d', d => {
                    return `M${d.x},${d.y}C${d.x},${(d.y + d.parent.y) / 2} ${d.parent.x},${(d.y + d.parent.y) / 2} ${d.parent.x},${d.parent.y}`;
                });
            
            // צור קבוצה לכל צומת
            const node = svg.selectAll('.node')
                .data(nodes)
                .enter().append('g')
                .attr('class', 'node')
                .attr('transform', d => `translate(${d.x},${d.y})`)
                .on('click', (event, d) => {
                    if (d.data && d.data.id) {
                        loadFamilyTree(d.data.id);
                    }
                });
            
            // הוסף עיגול לכל צומת
            node.append('circle')
                .attr('r', 10)
                .style('fill', d => d.data.id === currentPersonId ? '#4fc3f7' : '#fff');
            
            // הוסף טקסט לכל צומת
            node.append('text')
                .attr('dy', '.31em')
                .attr('x', d => d.children ? -15 : 15)
                .style('text-anchor', d => d.children ? 'end' : 'start')
                .text(d => `${d.data.first_name} ${d.data.last_name}`);
        }
        
        function zoomed(event) {
            svg.attr('transform', event.transform);
        }
    }
    
    // פונקציית עזר לבניית היררכיה לעץ
    function buildHierarchy(data) {
        const mainPerson = {
            id: data.main_person.id,
            first_name: data.main_person.first_name,
            last_name: data.main_person.last_name,
            title: data.main_person.title
        };
        
        const root = {data: mainPerson, children: []};
        
        // הוסף אב אם קיים
        if (data.father) {
            root.children.push({
                data: data.father,
                children: []
            });
            
            // הוסף אחים אם קיימים
            if (data.siblings && data.siblings.length > 0) {
                data.siblings.forEach(sibling => {
                    root.children[0].children.push({
                        data: sibling
                    });
                });
            }
            
            // הוסף את האדם הנוכחי כילד של האב
            root.children[0].children.push({
                data: mainPerson,
                children: []
            });
        }
        
        // הוסף חותן אם קיים
        if (data.father_in_law) {
            const fatherInLawNode = {
                data: data.father_in_law,
                children: []
            };
            
            // הוסף גיסים אם קיימים
            if (data.brothers_in_law && data.brothers_in_law.length > 0) {
                data.brothers_in_law.forEach(brother => {
                    fatherInLawNode.children.push({
                        data: brother
                    });
                });
            }
            
            root.children.push(fatherInLawNode);
        }
        
        // הוסף ילדים אם קיימים
        if (data.children && data.children.length > 0) {
            const childrenNode = root.children.find(c => c.data.id === mainPerson.id) || root;
            
            data.children.forEach(child => {
                childrenNode.children.push({
                    data: child
                });
            });
        }
        
        return d3.hierarchy(root);
    }
    
    // הצג פרטי אדם במודל
    function showPersonDetails(person) {
        if (!personModal || !personInfo) {
            console.error('Modal elements not found');
            return;
        }

        document.getElementById('modalTitle').textContent = `${person.title || ''} ${person.first_name} ${person.last_name}`;
        
        let html = `
            <div class="info-row">
                <div class="info-label">כתובת:</div>
                <div class="info-value">${person.address || 'לא צוין'}</div>
            </div>
            <div class="info-row">
                <div class="info-label">טלפון:</div>
                <div class="info-value">${person.phone || 'לא צוין'}</div>
            </div>
            <div class="info-row">
                <div class="info-label">נייד:</div>
                <div class="info-value">${person.mobile || 'לא צוין'}</div>
            </div>
        `;
        
        personInfo.innerHTML = html;
        personModal.style.display = 'block';
    }
    
    // פונקציות זום
    function zoomIn() {
        if (!d3.select('#familyTree svg').node()) return;
        d3.select('#familyTree svg').transition().call(zoomListener.scaleBy, 1.2);
    }
    
    function zoomOut() {
        if (!d3.select('#familyTree svg').node()) return;
        d3.select('#familyTree svg').transition().call(zoomListener.scaleBy, 0.8);
    }
    
    function resetView() {
        if (!d3.select('#familyTree svg').node()) return;
        d3.select('#familyTree svg').transition()
            .duration(750)
            .call(zoomListener.transform, d3.zoomIdentity);
    }
});