package com.example.databaseimport;

import com.example.databaseimport.service.CsvImportService;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

import java.nio.file.Paths;

@SpringBootApplication
public class DatabaseImportApplication {

    public static void main(String[] args) {
        SpringApplication.run(DatabaseImportApplication.class, args);
    }
    
    @Bean
    public CommandLineRunner commandLineRunner(CsvImportService csvImportService) {
        return args -> {
            // 设置CSV文件路径 - 使用当前目录下的文件
            String roomCsvPath = Paths.get("room.csv").toAbsolutePath().toString();
            String studentCsvPath = Paths.get("student.csv").toAbsolutePath().toString();
            
            // 如果命令行传入了参数，则使用命令行参数
            if (args.length >= 2) {
                roomCsvPath = args[0];
                studentCsvPath = args[1];
            }
            
            System.out.println("开始初始化数据库...");
            System.out.println("Room CSV 路径: " + roomCsvPath);
            System.out.println("Student CSV 路径: " + studentCsvPath);
            
            // 初始化数据库
            csvImportService.initializeDatabase(roomCsvPath, studentCsvPath);
            
            System.out.println("数据库初始化完成！");
        };
    }
} 