document.addEventListener('DOMContentLoaded', (): void => {
  
  // 1. Header scroll effect
  const header: HTMLElement | null = document.querySelector('header');
  window.addEventListener('scroll', (): void => {
    if (header) {
      if (window.scrollY > 50) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }
    }
  });

  // 2. Scroll Reveal Animations
  const revealElements: NodeListOf<HTMLElement> = document.querySelectorAll('.reveal');
  const revealObserver: IntersectionObserver = new IntersectionObserver((entries: IntersectionObserverEntry[], observer: IntersectionObserver): void => {
    entries.forEach((entry: IntersectionObserverEntry): void => {
      if (entry.isIntersecting) {
        entry.target.classList.add('active');
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.15,
    rootMargin: '0px 0px -50px 0px'
  });

  revealElements.forEach((el: HTMLElement): void => revealObserver.observe(el));

  // 3. Hero Typing Effect
  const typingTextContainer: HTMLElement | null = document.querySelector('.typing-text');
  if (typingTextContainer) {
    const fullHTML: string = typingTextContainer.innerHTML.trim();
    typingTextContainer.innerHTML = '';
    
    let i: number = 0;
    const speed: number = 95; // Typing speed in milliseconds per character
    
    const type = (): void => {
      if (i < fullHTML.length) {
        if (fullHTML[i] === '<') {
          const tagEnd: number = fullHTML.indexOf('>', i);
          if (tagEnd !== -1) {
            typingTextContainer.innerHTML = fullHTML.substring(0, tagEnd + 1);
            i = tagEnd + 1;
          } else {
            typingTextContainer.innerHTML = fullHTML.substring(0, i + 1);
            i++;
          }
        } else {
          typingTextContainer.innerHTML = fullHTML.substring(0, i + 1);
          i++;
        }
        setTimeout(type, speed);
      } else {
        const heroSection: HTMLElement | null = document.querySelector('.hero');
        if (heroSection) {
          heroSection.classList.add('typing-complete');
        }
      }
    };
    
    setTimeout(type, 450);
  }

  // 4. Team Matcher Demo
  initTeamMatcherDemo();

  // 5. Interactive Liquid Background
  try {
    initInteractiveBackground();
  } catch (err) {
    console.error("Error initializing interactive background:", err);
  }
});

// Team Matcher Demo Logic
function initTeamMatcherDemo(): void {
  const categorySelect: HTMLSelectElement | null = document.getElementById('team-category') as HTMLSelectElement;
  const frequencySelect: HTMLSelectElement | null = document.getElementById('team-frequency') as HTMLSelectElement;
  const roleSelect: HTMLSelectElement | null = document.getElementById('team-role') as HTMLSelectElement;
  const sizeSelect: HTMLSelectElement | null = document.getElementById('team-size') as HTMLSelectElement;
  
  const matchBtn: HTMLButtonElement | null = document.getElementById('team-match-btn') as HTMLButtonElement;
  const matchResult: HTMLElement | null = document.getElementById('team-match-result');
  
  const matchAvatar: HTMLElement | null = document.getElementById('team-match-avatar');
  const matchName: HTMLElement | null = document.getElementById('team-match-name');
  const matchDept: HTMLElement | null = document.getElementById('team-match-dept');
  const matchScore: HTMLElement | null = document.getElementById('team-match-score');
  
  const compGoal: HTMLElement | null = document.getElementById('comp-bar-goal');
  const compTime: HTMLElement | null = document.getElementById('comp-bar-time');
  const compComplement: HTMLElement | null = document.getElementById('comp-bar-complement');
  const analysisText: HTMLElement | null = document.getElementById('team-match-analysis-text');

  if (matchBtn && categorySelect && frequencySelect && roleSelect && sizeSelect && matchResult) {
    matchBtn.addEventListener('click', (): void => {
      matchBtn.disabled = true;
      matchBtn.innerHTML = '⚡ AI 협업 시너지 분석 중...';
      matchResult.classList.add('hidden');
      
      const category: string = categorySelect.value;
      const frequency: string = frequencySelect.value;
      const role: string = roleSelect.value;
      const size: string = sizeSelect.value;
      
      setTimeout((): void => {
        let teamName: string = '해커톤 준비팀 "데브캠퍼스"';
        let leaderName: string = '팀장: 김민우 (컴퓨터공학과)';
        let teamAvatar: string = '데';
        
        let goalFit: number = 95;
        let timeFit: number = 90;
        let complementFit: number = 95;
        
        let analysisMsg: string = '';
        
        if (category === 'study') {
          teamName = '전공 A+ 보장 스터디 "에이플러스"';
          leaderName = '팀장: 이서윤 (경영학과)';
          teamAvatar = '에';
          analysisMsg = '선택하신 전공 학술 스터디에 맞추어, 성실한 출석과 학술 논문/자료 공유가 활발히 이뤄지는 검증된 학습 팀을 추천합니다. ';
        } else if (category === 'startup') {
          teamName = '대학생 창업 공모전 팀 "이노베이터"';
          leaderName = '팀장: 최성준 (경제학과)';
          teamAvatar = '이';
          analysisMsg = '비즈니스 공모전 출전 및 예비 창업 트랙을 목표로, 사업 계획서 작성 및 피칭 훈련을 고도화하는 실무형 팀입니다. ';
        } else if (category === 'sports') {
          teamName = '친선 스포츠/러닝 모임 "러닝캠퍼스"';
          leaderName = '팀장: 박진우 (체육학과)';
          teamAvatar = '러';
          analysisMsg = '정기적인 아침 러닝 및 학과 대항전 친선 경기를 대비해, 부담 없이 친목을 다지고 에너지를 나누는 소모임입니다. ';
        } else {
          teamName = '해커톤 준비팀 "데브캠퍼스"';
          leaderName = '팀장: 김민우 (컴퓨터공학과)';
          teamAvatar = '데';
          analysisMsg = 'IT/소프트웨어 개발 분야의 해커톤 및 프로토타입 완성을 최우선 목표로 삼고 맹렬히 달리는 실전 사이드 프로젝트 팀입니다. ';
        }
        
        if (role === 'leader') {
          goalFit = 98;
          analysisMsg += '특히 리더로서 팀의 마일스톤을 리드하고 회의 아젠다를 조율하고 싶어 하시는 성향은, 현재 주도적인 기획자를 절실히 필요로 하는 이 팀의 방향성과 98%의 극적인 목표 일치도를 보입니다. ';
        } else if (role === 'creator') {
          goalFit = 94;
          analysisMsg += '창의적인 시각 디자인 및 아이디어 브레인스토밍을 담당해 줄 크리에이터의 영입이 시급한 상황이었기에, 귀하의 디자인적 관점이 팀의 완성도를 극대화할 것입니다. ';
        } else {
          goalFit = 91;
          analysisMsg += '묵묵히 실무를 수행하고 조화로운 개발/문서화를 이어가는 성실한 조력자 성향은, 팀 리더의 마일스톤 기획과 만나 완벽한 실행력을 뿜어냅니다. ';
        }
        
        if (frequency === 'high') {
          timeFit = 96;
          analysisMsg += '또한 매일 혹은 주 3회 이상의 높은 몰입도로 기여 가능한 시간 요건을 선호하므로, 단기 완성 및 집중 개발 스프린트 일정과 정확하게 매칭됩니다.';
        } else if (frequency === 'low') {
          timeFit = 85;
          analysisMsg += '과도한 시간 부담 없이 자유로운 개인 시간 스케줄에 맞춰 참여하기를 희망하시므로, 상호 간의 비동기 커뮤니케이션과 유연한 분담 태스크 기반으로 조율됩니다.';
        } else {
          timeFit = 92;
          analysisMsg += '주 1~2회 정기 세션 및 격주 오프라인 모임의 라이트하고 성실한 템포로 조율되어 있어, 학업 및 타 전공 스케줄과 원활하게 병행이 가능합니다.';
        }
        
        if (size === 'small') {
          complementFit = 97;
          analysisMsg += ' 소수 정예(2~3명)의 기민한 커뮤니케이션으로 소통 비용을 아끼고, 끈끈하고 돈독한 개인적 신뢰와 코드 리뷰, 빠른 피드백 루프를 통해 성과를 일궈낼 것입니다.';
        } else if (size === 'large') {
          complementFit = 82;
          analysisMsg += ' 10명 이상의 비교적 대규모 학과 네트워크 안에서 다양한 전공 배경의 인물들과 교류하며, 넓은 시야와 풍부한 인적 자원 시너지를 확보할 수 있습니다.';
        } else {
          complementFit = 92;
          analysisMsg += ' 4~6명 내외의 역할 분담이 확실하게 보장되는 건강한 팀 빌딩으로, 기획/개발/디자인이 각각 유기적으로 작용하여 밸런스 있는 협업이 연출됩니다.';
        }
        
        const avgScore: number = Math.round((goalFit + timeFit + complementFit) / 3);
        
        if (matchName) matchName.textContent = teamName;
        if (matchDept) matchDept.textContent = leaderName;
        if (matchAvatar) matchAvatar.textContent = teamAvatar;
        if (matchScore) matchScore.textContent = `${avgScore}%`;
        
        matchResult.classList.remove('hidden');
        
        setTimeout((): void => {
          if (compGoal) compGoal.style.width = `${goalFit}%`;
          if (compTime) compTime.style.width = `${timeFit}%`;
          if (compComplement) compComplement.style.width = `${complementFit}%`;
        }, 50);
        
        matchBtn.disabled = false;
        matchBtn.innerHTML = '<i class="ri-magic-line"></i> AI 소모임/프로젝트 매칭 시작';
        
        if (analysisText) {
          analysisText.innerHTML = '';
          let charIndex: number = 0;
          
          const typeTeamText = (): void => {
            if (charIndex < analysisMsg.length) {
              analysisText.innerHTML += analysisMsg[charIndex];
              charIndex++;
              setTimeout(typeTeamText, 15);
            }
          };
          typeTeamText();
        }
        
      }, 1200);
    });
  }
}

// Interactive Liquid Background Logic
function initInteractiveBackground(): void {
  console.log("CreditCampus: Initializing Interactive Liquid Background...");
  const interactiveBlob: HTMLElement | null = document.querySelector('.blob-interactive');
  const heroSection: HTMLElement | null = document.querySelector('.hero');
  
  if (!interactiveBlob || !heroSection) {
    console.warn("CreditCampus: Scoped liquid background elements not found in DOM.");
    return;
  }
  console.log("CreditCampus: Scoped .blob-interactive element initialized.");

  let currentX: number = window.innerWidth / 2;
  let currentY: number = 300; // Approximate half height of hero
  let targetX: number = currentX;
  let targetY: number = currentY;

  // Track mouse movements relative to the Hero section
  window.addEventListener('mousemove', (e: MouseEvent): void => {
    const rect: DOMRect = heroSection.getBoundingClientRect();
    targetX = e.clientX - rect.left;
    targetY = e.clientY - rect.top;
  });

  // Track touches for touch devices relative to the Hero section
  window.addEventListener('touchmove', (e: TouchEvent): void => {
    if (e.touches.length > 0) {
      const rect: DOMRect = heroSection.getBoundingClientRect();
      targetX = e.touches[0].clientX - rect.left;
      targetY = e.touches[0].clientY - rect.top;
    }
  });

  // Linear Interpolation (Lerp) for gooey smooth tracking
  const speed: number = 0.05; 
  const updatePosition = (): void => {
    currentX += (targetX - currentX) * speed;
    currentY += (targetY - currentY) * speed;

    interactiveBlob.style.transform = `translate3d(${currentX}px, ${currentY}px, 0)`;
    
    requestAnimationFrame(updatePosition);
  };

  updatePosition();
}
