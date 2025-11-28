'''
# 필수 도구 설치 (macOS)
brew install imagemagick potrace

# 또는 Ubuntu/Debian
sudo apt-get install imagemagick potrace

# 테스트 실행
python src/utils/svg_utils.py
'''

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional

def png_to_svg(input_png_path: str, output_svg_path: str) -> bool:
    """
    PNG 이미지를 potrace CLI를 통해 SVG로 변환
    
    Args:
        input_png_path: 입력 PNG 파일 경로
        output_svg_path: 출력 SVG 파일 경로
    
    Returns:
        변환 성공 여부
    """
    try:
        input_path = Path(input_png_path)
        output_path = Path(output_svg_path)
        
        if not input_path.exists():
            print(f"입력 파일이 존재하지 않습니다: {input_png_path}")
            return False
        
        # 1. PNG → PGM 변환 (ImageMagick convert 사용)
        pgm_path = input_path.with_suffix('.pgm')
        subprocess.run([
            'convert', str(input_path), 
            '-monochrome', '-threshold', '50%', 
            str(pgm_path)
        ], check=True, capture_output=True)
        
        # 2. potrace 호출 (PGM → SVG)
        subprocess.run([
            'potrace', str(pgm_path),
            '-s', '--svg',
            '-o', str(output_path)
        ], check=True, capture_output=True)
        
        # 임시 PGM 파일 정리
        pgm_path.unlink(missing_ok=True)
        
        print(f"변환 완료: {input_png_path} → {output_svg_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"potrace 변환 실패: {e}")
        return False
    except FileNotFoundError as e:
        print(f"필수 도구 누락 (ImageMagick/potrace): {e}")
        return False
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return False

def clean_svg(svg_path: str, output_path: Optional[str] = None) -> bool:
    """
    SVG 파일을 정리합니다. (TODO: 구현 예정)
    
    현재는 단순 복사만 수행합니다.
    향후 구현 가능 항목:
    - path 데이터 압축/최적화
    - 불필요한 속성 제거
    - 노이즈 path 필터링
    
    Args:
        svg_path: 입력 SVG 파일 경로
        output_path: 출력 SVG 파일 경로 (None이면 원본 덮어쓰기)
    
    Returns:
        정리 성공 여부
    """
    try:
        input_path = Path(svg_path)
        output_path = Path(output_path) if output_path else input_path
        
        if not input_path.exists():
            print(f"SVG 파일이 존재하지 않습니다: {svg_path}")
            return False
        
        # TODO: 실제 SVG 정리 로직 구현
        # 현재는 단순 복사
        shutil.copy2(input_path, output_path)
        print(f"SVG 정리 완료: {svg_path} → {output_path}")
        return True
        
    except Exception as e:
        print(f"SVG 정리 실패: {e}")
        return False

def batch_convert_png_to_svg(input_dir: str, output_dir: str) -> int:
    """
    디렉토리 내 모든 PNG 파일을 배치 변환합니다.
    
    Args:
        input_dir: 입력 PNG 파일들이 있는 디렉토리
        output_dir: 출력 SVG 파일들이 저장될 디렉토리
    
    Returns:
        성공적으로 변환된 파일 수
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # 출력 디렉토리 생성
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        print(f"입력 디렉토리가 존재하지 않습니다: {input_dir}")
        return 0
    
    png_files = list(input_path.glob("*.png"))
    if not png_files:
        print(f"PNG 파일을 찾을 수 없습니다: {input_dir}")
        return 0
    
    success_count = 0
    for png_file in png_files:
        svg_file = output_path / f"{png_file.stem}.svg"
        
        if png_to_svg(str(png_file), str(svg_file)):
            # clean_svg 호출 (선택적)
            clean_svg(str(svg_file))
            success_count += 1
    
    print(f"배치 변환 완료: {success_count}/{len(png_files)} 파일 성공")
    return success_count

# 사용 예시
if __name__ == "__main__":
    # 단일 파일 변환 테스트
    png_to_svg("input.png", "output.svg")
    
    # 배치 변환 테스트
    # batch_convert_png_to_svg("./pngs", "./svgs")
    pass
