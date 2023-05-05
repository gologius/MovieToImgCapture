# -*- coding: utf-8 -*-
"""
Created on Fri May  5 10:01:03 2023
"""

import cv2
import numpy as np
import os
import sys

class MovieToTimgCapture:
    
    MAIN_WIN_NAME = "MovieToImgCapture"
    SEEKBAR_NAME = "frame"
    
    lookIndex = 0
    playing = True
    
    def update_seekbar(self, value):
        """
        シークバーが更新された際に呼び出される関数。
        更新された場合は、参照すべきフレーム数も更新する
        """        
        self.lookIndex = cv2.getTrackbarPos(self.SEEKBAR_NAME, self.MAIN_WIN_NAME)
        return
        
    def update_look_frame(self, maxFrameCount, add_value):
        """
        現在参照しているフレーム数から、別のフレームに移動する際に使用する
        
        Args:            
            maxFrameCount: 動画の最大フレーム数
            
            add_value: 現在フレームからの加算フレーム値

        Return:
            最終的に参照することになったフレーム
        """
        
        nextIndex = self.lookIndex + add_value
        if nextIndex > maxFrameCount:
            nextIndex = maxFrameCount
        elif nextIndex < 0:
            nextIndex = 0
                
        self.lookIndex = nextIndex

        return self.lookIndex
        
    def draw_log_text(self, img, text_list, margin=20, offset=(20,20)):
        """
        string型のリストを引数として、画面上にテキストを描画する。
        デバッグ用。
        """
        
        #最大文字数を計算
        max_char_num = 0
        for t in text_list:
            if len(t) > max_char_num:
                max_char_num = len(t)
        
        max_x = 10 * max_char_num + offset[0]
        max_y = margin * len(text_list) + offset[1]  
        
        #背景色用の四角形
        cv2.rectangle(img, (0,0), (max_x, max_y), (30,30,30), thickness=-1)
        
        #リストにある文字列を順番に出力する
        for i,t in enumerate(text_list):
            cv2.putText(img, t, (offset[0], i*margin + offset[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1, cv2.LINE_AA);        
  
        return
        
    def exec_loop(self, readFilePath, saveDir, skip_frame=480):
        
        #動画読み込み
        video = cv2.VideoCapture(readFilePath)
        maxFrameCount = int(video.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
        fps = video.get(cv2.CAP_PROP_FPS)      
        wait_frame = int(1000 / fps)
        max_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        max_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"read: {readFilePath}")
        print(f"max frame count:{maxFrameCount} fps:{fps} size:{(max_width,max_height)}")

        try:        
            #OpenCV設定
            cv2.namedWindow(self.MAIN_WIN_NAME, cv2.WINDOW_AUTOSIZE | cv2.WINDOW_KEEPRATIO)
            cv2.createTrackbar(self.SEEKBAR_NAME, self.MAIN_WIN_NAME, 0, maxFrameCount, self.update_seekbar)
            
            #操作ループ 
            img = None
            workimg = None
            while True:
                
                #表示希望しているインデックスと、現在のインデックスに乖離があれば、その位置までインデックスを動かす
                #※毎フレームsetすると、処理が遅くなるため、変化がある場合のみ処理する
                if self.lookIndex != video.get(cv2.CAP_PROP_POS_FRAMES):
                    video.set(cv2.CAP_PROP_POS_FRAMES, self.lookIndex)    
                
                #トラックバーで指定されたフレームに移動し，画像を一枚読み込む
                success, img = video.read()
                workimg = np.array(img)
                if success == False:
                     # 読み込みに失敗した場合はスキップして次のフレームに進む
                    self.update_look_frame(maxFrameCount, +1)    
                    continue
                elif self.playing:
                    # 再生中の場合のみ、次のフレームに進む
                    self.update_look_frame(maxFrameCount, +1)
                
                #キー入力チェック
                key = cv2.waitKey(wait_frame)
                is_captured = False
                if key >= 0: #未入力の場合は-1が返却される
                	#フレーム戻る
                    if key == ord("a"):
                        self.update_look_frame(maxFrameCount, -skip_frame)
                    #フレーム進める
                    elif key == ord("d"):
                        self.update_look_frame(maxFrameCount, +skip_frame)       
                    #画像保存
                    elif key == ord("s"):
                        basename_without_ext = os.path.splitext(os.path.basename(readFilePath))[0]
                        tmp_path = f"{saveDir}\\tmp.png"
                        dst_path = f"{saveDir}\\{basename_without_ext}_{self.lookIndex}.png"
                        
                        #opencvが日本語対応していないため、一度適当なファイル名で保存してから、リネームする
                        cv2.imwrite(tmp_path, img) #保存されるのはworkではなく元画像になるため注意
                        if os.path.isfile(dst_path):
                            os.remove(dst_path) #ファイルが存在している場合は削除する
                            print(f"file is existed!! remove file: {dst_path}")
                        os.rename(tmp_path ,dst_path)
                        is_captured = True #結果表示に使用するフラグ
    
                        print(f"save img: {dst_path}")
                        
                    #再生/一時停止
                    elif key == 32: #spaceキー
                        self.playing = not self.playing
                    #終了        
                    elif key == ord("q"):
                        break        
                
                #描画のためのテキストリストを作成
                logs = []
                logs.append(f"Frame:{self.lookIndex}/{maxFrameCount}")
                logs.append(f"a:<- d:-> s:saveimg space:play/pause q:quit")
                if self.playing:
                    logs.append("Play")
                else:
                    logs.append("Pause")
                  
                if is_captured == True:
                    logs.append("Save Image !!")
                
                #描画
                self.draw_log_text(workimg, logs)
                cv2.imshow(self.MAIN_WIN_NAME, workimg)
                cv2.setTrackbarPos(self.SEEKBAR_NAME, self.MAIN_WIN_NAME, self.lookIndex)
                
        except Exception as e:
            raise e            
        finally:
            video.release()    
            cv2.destroyAllWindows()
        
        return

def main():
    print(f"引数 {sys.argv}")
    
    if len(sys.argv) != 3:
        print("引数エラー。引数には、元動画のファイルパスと、保存先のファイルパスが必要です。")
        return
    
    movie_path = sys.argv[1]
    save_dir = sys.argv[2]
    
    tmp = MovieToTimgCapture()
    tmp.exec_loop(movie_path, save_dir)

    return

main()