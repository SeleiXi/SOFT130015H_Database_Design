## Github link: https://github.com/SeleiXi/SOFT130015H_Database_Design

--- 

## How to run

1. Docker
```shell
docker pull seleixi/soft130059:latest
docker run -it seleixi/soft130059:latest
```
2. Maven
```shell
mvn clean package
java -jar target/database-import-0.0.1-SNAPSHOT.jar
```

## 运行截图
见本文件根目录，或者 https://github.com/SeleiXi/FDU-SOFT130059-Object-Oriented-Programming 的README

---
## 说明

项目使用到原生SQL语句，问过吴老师，用MyBatis没问题~

```java
package com.example.databaseimport.mapper;

import com.example.databaseimport.entity.Room;
import org.apache.ibatis.annotations.*;
import java.util.List;

@Mapper
public interface RoomMapper {
    
    @Update({
        "CREATE TABLE IF NOT EXISTS room (",
        "  kdno VARCHAR(10) NOT NULL,",
        "  kcno INT NOT NULL,",
        "  ccno INT NOT NULL,",
        "  kdname VARCHAR(50),",
        "  exptime DATETIME,",
        "  papername VARCHAR(50),",
        "  PRIMARY KEY (kdno, kcno, ccno)",
        ")"
    })
    void createTable();
    
    @Insert({
        "INSERT INTO room(kdno, kcno, ccno, kdname, exptime, papername)",
        "VALUES(#{kdno}, #{kcno}, #{ccno}, #{kdname}, #{exptime}, #{papername})"
    })
    void insert(Room room);
    
    @Insert({
        "<script>",
        "INSERT INTO room(kdno, kcno, ccno, kdname, exptime, papername) VALUES",
        "<foreach collection='list' item='item' separator=','>",
        "(#{item.kdno}, #{item.kcno}, #{item.ccno}, #{item.kdname}, #{item.exptime}, #{item.papername})",
        "</foreach>",
        "</script>"
    })
    void batchInsert(@Param("list") List<Room> rooms);
    
    @Select("SELECT COUNT(*) FROM room")
    int count();
    
    @Select("SELECT * FROM room LIMIT 10")
    List<Room> selectSample();
} 
```

```java

package com.example.databaseimport.mapper;

import com.example.databaseimport.entity.Student;
import org.apache.ibatis.annotations.*;
import java.util.List;

@Mapper
public interface StudentMapper {
    
    @Update({
        "CREATE TABLE IF NOT EXISTS student (",
        "  registno VARCHAR(20) NOT NULL,",
        "  name VARCHAR(50),",
        "  kdno VARCHAR(10) NOT NULL,",
        "  kcno INT NOT NULL,",
        "  ccno INT NOT NULL,",
        "  seat INT,",
        "  PRIMARY KEY (registno),",
        "  FOREIGN KEY (kdno, kcno, ccno) REFERENCES room(kdno, kcno, ccno)",
        ")"
    })
    void createTable();
    
    @Insert({
        "INSERT INTO student(registno, name, kdno, kcno, ccno, seat)",
        "VALUES(#{registno}, #{name}, #{kdno}, #{kcno}, #{ccno}, #{seat})"
    })
    void insert(Student student);
    
    @Insert({
        "<script>",
        "INSERT INTO student(registno, name, kdno, kcno, ccno, seat) VALUES",
        "<foreach collection='list' item='item' separator=','>",
        "(#{item.registno}, #{item.name}, #{item.kdno}, #{item.kcno}, #{item.ccno}, #{item.seat})",
        "</foreach>",
        "</script>"
    })
    void batchInsert(@Param("list") List<Student> students);
    
    @Select("SELECT COUNT(*) FROM student")
    int count();
    
    @Select("SELECT * FROM student LIMIT 10")
    List<Student> selectSample();
} 
```


